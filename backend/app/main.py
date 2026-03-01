import time
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from app.api import api_router
from contextlib import asynccontextmanager
import uuid

from ml.predictor import FinAccessPredictor
from app.services.model_service import ModelService
from app.services.inference_engine import InferenceEngine
from app.cache.redis_client import get_redis_client
from app.core.metrics import MetricsCollector
from app.core.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load heavily on startup ONCE
    try:
        predictor = FinAccessPredictor()
        logger.info("FinAccessPredictor loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load FinAccessPredictor: {e}")
        raise e

    model_service = ModelService(predictor)
    inference_engine = InferenceEngine(model_service)
    
    app.state.model_service = model_service
    app.state.inference_engine = inference_engine
    
    # Init system extensions
    app.state.metrics = MetricsCollector()
    app.state.redis = await get_redis_client()
    
    logger.info("Application started. ML Model & extensions initialized.")
    yield
    # Shutdown safely
    await app.state.redis.aclose()
    inference_engine.shutdown()

app = FastAPI(
    title="Financial Risk Scoring System API",
    description="High-performance backend for financial risk scoring.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next: Callable) -> Response:
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()
    
    # Store request_id for contextual logging inside routes if needed
    request.state.request_id = request_id
    
    response = await call_next(request)
    
    process_time = time.perf_counter() - start_time
    latency_ms = process_time * 1000
    
    # Update global metrics aggregator
    if hasattr(request.app.state, "metrics"):
        request.app.state.metrics.increment_requests()
        request.app.state.metrics.record_latency(latency_ms)
        
        # Track threads passively if using threaded mode
        if hasattr(request.app.state, "inference_engine"):
            request.app.state.metrics.set_active_threads(
                len(request.app.state.inference_engine.thread_pool._threads)
            )

    client_ip = request.client.host if request.client else "Unknown"
    
    # Dispatch structured log utilizing dynamic record attributes
    logger.info(
        f"[{request.method}] {client_ip} {response.status_code}",
        extra={
            "request_id": request_id,
            "endpoint": request.url.path,
            "latency_ms": round(latency_ms, 2)
        }
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "-")
    logger.error(
        f"Unhandled Exception: {exc}",
        extra={
            "request_id": request_id,
            "endpoint": request.url.path,
            "latency_ms": "-"
        }
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

# Routers
app.include_router(api_router)

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok"}
