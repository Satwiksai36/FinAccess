import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any
import logging

from app.services.model_service import BaseModelService
from app.core.config import settings

logger = logging.getLogger(__name__)

class InferenceEngine:
    def __init__(self, model_service: BaseModelService):
        """
        Initializes the inference engine with a concrete ModelService
        and dynamically sizes the thread pool strictly to 2 * CPU cores.
        """
        self.model_service = model_service
        
        if str(settings.THREADPOOL_WORKERS).lower() == "auto":
            self.max_workers = (os.cpu_count() or 1) * 2
        else:
            try:
                self.max_workers = int(settings.THREADPOOL_WORKERS)
            except ValueError:
                self.max_workers = (os.cpu_count() or 1) * 2
        
        logger.info(f"Initializing InferenceEngine ThreadPoolExecutor with {self.max_workers} workers.")
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        
    async def run_inference(self, app, raw_input: dict[str, Any]) -> dict[str, Any]:
        """
        Runs the CPU-heavy inference payload inside the ThreadPoolExecutor
        to avoid blocking the main asyncio event loop.
        """
        loop = asyncio.get_running_loop()
        # run_in_executor automatically offloads the blocking call
        result = await loop.run_in_executor(
            self.thread_pool, 
            app.state.model_service.predict,
            raw_input
        )
        return result
        
    def shutdown(self):
        """Graceful shutdown for the threadpool"""
        self.thread_pool.shutdown(wait=True)
