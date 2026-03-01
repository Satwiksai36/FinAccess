from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ModelScores(BaseModel):
    tabular: float
    temporal: float
    graph: float

class TopFeature(BaseModel):
    feature: str
    shap_value: float
    direction: str

class PredictionResponse(BaseModel):
    """
    Full ML prediction result returned by the /predict/{applicant_id} endpoint.

    Fields
    ------
    risk_score      : Final fused risk score in [0, 1]. Higher = higher default risk.
    risk_label      : Human-readable band — LOW | MEDIUM | HIGH.
    decision        : Lending decision — APPROVED | REJECTED.
    model_scores    : Individual scores from tabular (XGBoost), temporal (BiLSTM), graph (GCN).
    graph_influence : |graph_score − final_score| — magnitude of GNN impact on the fusion result.
    graph_source    : 'trained_gcn' or 'proxy_xgb_bilstm' (cold-start fallback).
    top_features    : Top-N SHAP feature attributions from the XGBoost model.
    attention_weights: BiLSTM temporal attention distribution across input segments.
    summary         : Human-readable explanation string.
    inference_time_ms: End-to-end latency in milliseconds.
    """
    applicant_id: int
    risk_score: float
    risk_label: str
    decision: str
    model_scores: ModelScores
    graph_influence: Optional[float] = Field(
        default=None,
        description="Absolute difference between GCN graph score and final fusion output."
    )
    graph_source: Optional[str] = Field(
        default=None,
        description="'trained_gcn' if real GCN loaded, else 'proxy_xgb_bilstm' cold-start."
    )
    top_features: List[TopFeature]
    attention_weights: Dict[str, float]
    summary: str
    inference_time_ms: float
