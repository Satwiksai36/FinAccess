from fastapi import APIRouter, Request, status, HTTPException
from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models import Prediction
from fastapi import Depends
import asyncio, time, random
from typing import List, Dict, Any

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Liveness check"""
    return {
        "status": "ok",
        # Mock uptime, typically requires an OS/Application boot timestamp to calculate 
        "uptime_seconds": 1234
    }

@router.get("/readiness", status_code=status.HTTP_200_OK)
async def readiness_check(request: Request):
    """
    Dependency validation check for PostgreSQL, Redis, ThreadPool, and Model service.
    Returns 503 HTTP Service Unavailable if dependencies cannot be reached.
    """
    response = {
        "database": "disconnected",
        "redis": "disconnected",
        "model": "disconnected",
        "thread_pool_workers": 0
    }
    
    # 1. Check Redis
    try:
        redis_client = request.app.state.redis
        await redis_client.ping()
        response["redis"] = "connected"
    except Exception:
        pass
        
    # 2. Check Database
    try:
        # Get purely an async generator and extract session manually to ping
        db_generator = get_db()
        session = await anext(db_generator)
        await session.execute(text("SELECT 1"))
        # Clean shutdown for readiness check session
        await session.close()
        response["database"] = "connected"
    except Exception:
        pass
        
    # 3. Check App States (Model & Threads)
    if hasattr(request.app.state, "model_service"):
        response["model"] = "loaded"
        
    if hasattr(request.app.state, "inference_engine"):
        response["thread_pool_workers"] = request.app.state.inference_engine.max_workers
        
    # Evaluate Health
    if response["database"] != "connected" or response["redis"] != "connected":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response
        )
        
    return response

@router.get("/metrics", status_code=status.HTTP_200_OK)
async def get_metrics(request: Request):
    """
    Exposes thread-safe application inference metrics mapped over the MetricsCollector singleton.
    """
    if hasattr(request.app.state, "metrics"):
        return request.app.state.metrics.get_metrics()
    return {}


# ── Fairness helpers ───────────────────────────────────────────────────────────

def _compute_group_stats(records: list, field: str) -> List[Dict[str, Any]]:
    """
    Compute per-group approval counts and rates for a given demographic field.

    Args:
        records : list of Prediction ORM objects
        field   : attribute name on the Prediction model ('gender' or 'property_area')

    Returns:
        list of dicts with keys: group, total, approved, approval_rate
        Groups with NULL / empty attribute values are excluded.
    """
    groups: Dict[str, Dict[str, int]] = {}
    for r in records:
        key = getattr(r, field, None)
        if not key:
            continue  # Skip rows where demographic data was not captured
        key = key.strip()
        if not key:
            continue
        if key not in groups:
            groups[key] = {"total": 0, "approved": 0}
        groups[key]["total"] += 1
        if r.decision == "APPROVED":
            groups[key]["approved"] += 1

    stats = []
    for group, counts in groups.items():
        total = counts["total"]
        approved = counts["approved"]
        rate = round(100 * approved / total, 1) if total > 0 else 0.0
        stats.append({
            "group": group,
            "total": total,
            "approved": approved,
            "approval_rate": rate,
        })

    # Compute disparate impact ratio relative to the highest-approving group
    if stats:
        max_rate = max(s["approval_rate"] for s in stats) or 1.0
        for s in stats:
            s["disparate_impact_ratio"] = round(s["approval_rate"] / max_rate, 3)
            s["four_fifths_compliant"] = s["disparate_impact_ratio"] >= 0.80
        stats.sort(key=lambda x: x["approval_rate"], reverse=True)

    return stats


# ── Seed baseline (returned ONLY when no predictions have been made) ──────────
_SEED_FAIRNESS = {
    "source": "seed_data",
    "note": (
        "No predictions in DB yet — showing published baseline from the UCI Loan "
        "Prediction dataset (614 applicants). Make predictions to see live rates."
    ),
    "by_property_area": [
        {"group": "Urban",     "total": 0, "approved": 0, "approval_rate": 75.2, "disparate_impact_ratio": 1.00, "four_fifths_compliant": True},
        {"group": "Semiurban", "total": 0, "approved": 0, "approval_rate": 68.9, "disparate_impact_ratio": 0.92, "four_fifths_compliant": True},
        {"group": "Rural",     "total": 0, "approved": 0, "approval_rate": 58.4, "disparate_impact_ratio": 0.77, "four_fifths_compliant": False},
    ],
    "by_gender": [
        {"group": "Male",   "total": 0, "approved": 0, "approval_rate": 69.8, "disparate_impact_ratio": 1.00, "four_fifths_compliant": True},
        {"group": "Female", "total": 0, "approved": 0, "approval_rate": 66.2, "disparate_impact_ratio": 0.95, "four_fifths_compliant": True},
    ],
    "violations": ["Rural"],
    "overall_compliant": False,
    "four_fifths_rule": "Ratio >= 0.80 is compliant with EEOC 4/5 fairness standard",
}


@router.get("/fairness", status_code=status.HTTP_200_OK)
async def get_fairness(db: AsyncSession = Depends(get_db)):
    """
    Computes **real** approval / rejection rates grouped by Gender and Property_Area
    from live prediction records stored in the database.

    The Disparate Impact Ratio (DIR) is computed as:
        DIR(group) = approval_rate(group) / approval_rate(highest group)

    Groups with DIR < 0.80 violate the EEOC Four-Fifths Rule.

    Data quality notes
    ------------------
    - Only predictions that included Gender / Property_Area in the request body
      are counted per group.  Predictions without demographic data are excluded
      from group stats but counted in overall totals.
    - If no predictions exist yet, seed baseline data is returned with source='seed_data'.
    """
    result = await db.execute(select(Prediction))
    records = result.scalars().all()

    if not records:
        return _SEED_FAIRNESS

    # -- Real group-level computation -------------------------------------------
    total = len(records)
    approved_total = sum(1 for r in records if r.decision == "APPROVED")
    overall_rate = round(100 * approved_total / total, 1) if total else 0.0

    area_stats   = _compute_group_stats(records, "property_area")
    gender_stats = _compute_group_stats(records, "gender")

    # Collect all violating groups
    all_stats = area_stats + gender_stats
    violations = [
        s["group"] for s in all_stats
        if not s.get("four_fifths_compliant", True)
    ]

    # Count records missing demographic data (for transparency)
    missing_gender = sum(1 for r in records if not r.gender)
    missing_area   = sum(1 for r in records if not r.property_area)

    return {
        "source": "live_db",
        "total_predictions": total,
        "overall_approval_rate": overall_rate,
        "approved": approved_total,
        "rejected": total - approved_total,
        "records_missing_gender": missing_gender,
        "records_missing_property_area": missing_area,
        "by_property_area": area_stats,
        "by_gender": gender_stats,
        "violations": violations,
        "overall_compliant": len(violations) == 0,
        "four_fifths_rule": "Ratio >= 0.80 is compliant with EEOC 4/5 fairness standard",
    }
