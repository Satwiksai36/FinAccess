import logging
from abc import ABC, abstractmethod
from typing import Any
import torch

class BaseModelService(ABC):
    @abstractmethod
    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        """Runs the prediction synchronously"""
        pass

class ModelService(BaseModelService):
    def __init__(self, predictor):
        self.predictor = predictor

    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        """
        Executes CPU-bound machine learning workload.
        """
        with torch.no_grad():
            prediction = self.predictor.predict(features)
            
            try:
                explanation = self.predictor.explain(features)
            except Exception as e:
                logging.warning(f"Failed to generate SHAP explanation: {e}")
                explanation = {
                    "top_features": [],
                    "attention_weights": {},
                    "explanation_summary": "Explanation generation failed."
                }
                
        return {
            **prediction,
            **explanation
        }
