import time
import json
import hashlib
import hmac
import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import get_db
from app.database.models import Prediction
from app.schemas.prediction import PredictionResponse
from app.core.logger import logger

router = APIRouter()

# Exact set of feature keys the ML predictor.preprocess() reads.
# Keeping this as a module-level constant makes it easy to audit/update.
ML_LOAN_FIELDS = [
    "Gender", "Married", "Dependents", "Education", "Self_Employed",
    "ApplicantIncome", "CoapplicantIncome", "LoanAmount",
    "Loan_Amount_Term", "Credit_History", "Property_Area",
]

@router.post("/{applicant_id}", response_model=PredictionResponse)
async def predict_risk(
    applicant_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Computes a ML risk score for a given applicant.
    Accepts loan feature fields in the request body and runs them through
    the XGBoost + BiLSTM + GraphSAGE fusion pipeline.
    Implements a 300-second Redis cache keyed on (applicant_id + payload hash).
    """
    redis_client = request.app.state.redis
    request_id = getattr(request.state, "request_id", "-")

    # ── 1. Parse request body ────────────────────────────────────────────────
    body_data = {}
    try:
        body_data = await request.json()
    except Exception:
        pass

    # Build features dict with ONLY the keys the ML model expects.
    # Previously email/role/applicant_id were included here — the predictor
    # silently ignored them via .get() fallbacks, but they caused confusion
    # and made the cache key meaningless when only applicant_id was used.
    features = {k: body_data[k] for k in ML_LOAN_FIELDS if k in body_data}

    # ── 2. Cache lookup (keyed on applicant_id + payload content) ────────────
    # SHA256 hash of sorted payload ensures a deterministic, collision-resistant key.
    # Using SHA256 instead of MD5 for correctness in a financial security context.
    payload_hash = hashlib.sha256(
        json.dumps(features, sort_keys=True).encode()
    ).hexdigest()[:16]
    cache_key = f"prediction:{applicant_id}:{payload_hash}"

    cached_result = await redis_client.get(cache_key)
    if cached_result:
        logger.info(
            "CACHE_HIT",
            extra={"request_id": request_id, "endpoint": request.url.path, "latency_ms": "-"}
        )
        if hasattr(request.app.state, "metrics"):
            request.app.state.metrics.record_cache_hit()
        return PredictionResponse.model_validate_json(cached_result)

    if hasattr(request.app.state, "metrics"):
        request.app.state.metrics.record_cache_miss()

    # ── 3. Run ML inference ──────────────────────────────────────────────────
    inference_engine = request.app.state.inference_engine
    model_service = request.app.state.model_service

    start_time = time.perf_counter()

    if settings.INFERENCE_MODE == "threaded":
        prediction_result = await inference_engine.run_inference(request.app, features)
    else:
        prediction_result = model_service.predict(features)

    inference_time_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        "CACHE_MISS",
        extra={"request_id": request_id, "endpoint": request.url.path, "latency_ms": round(inference_time_ms, 2)}
    )
    if hasattr(request.app.state, "metrics"):
        request.app.state.metrics.record_ml_latency(inference_time_ms)

    # ── 4. Persist prediction to database ───────────────────────────────────
    risk_score = prediction_result.get("risk_score", 0.0)
    decision = prediction_result.get("decision", "UNKNOWN")
    model_scores = prediction_result.get("model_scores", {})
    explanation_summary = prediction_result.get("explanation_summary", "")

    # Extract demographic fields for fairness tracking.
    # These come from the loan application payload — capturing them at persist time
    # means the /system/fairness endpoint can compute real group-level approval rates.
    gender = str(body_data.get("Gender", "")).strip() or None
    property_area = str(body_data.get("Property_Area", "")).strip() or None

    prediction_record = Prediction(
        applicant_id=applicant_id,
        risk_score=risk_score,
        decision=decision,
        model_scores=model_scores,
        explanation_summary=explanation_summary,
        inference_time_ms=inference_time_ms,
        gender=gender,
        property_area=property_area,
    )
    db.add(prediction_record)
    await db.commit()
    await db.refresh(prediction_record)

    # ── 5. Build response and cache it (TTL = 300 s) ─────────────────────────
    response_payload = PredictionResponse(
        applicant_id=applicant_id,
        risk_score=risk_score,
        risk_label=prediction_result.get("risk_label", "UNKNOWN"),
        decision=decision,
        model_scores=model_scores,
        graph_influence=prediction_result.get("graph_influence"),
        graph_source=prediction_result.get("graph_source"),
        top_features=prediction_result.get("top_features", []),
        attention_weights=prediction_result.get("attention_weights", {}),
        summary=explanation_summary,
        inference_time_ms=inference_time_ms,
    )

    await redis_client.setex(cache_key, 300, response_payload.model_dump_json())

    return response_payload
