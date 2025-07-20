"""
SentimentSense - Main Sentiment Analysis Service Application
"""
import time
import uuid
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .models import (
    SentimentRequest,
    BatchSentimentRequest,
    SentimentResponse,
    BatchSentimentResponse,
    HealthResponse,
    ErrorResponse
)
from .sentiment import analyzer
from .logging_config import setup_logging, get_logger
from .metrics import metrics_middleware, get_metrics_endpoint, metrics_collector
from .health import health_checker, OverallHealth

# Setup structured logging
setup_logging()
logger = get_logger(__name__)

# Application start time
app_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("Starting SentimentSense service...")

    # Model warmup (optional)
    try:
        if analyzer.is_healthy():
            # Run a test analysis to warm up the model
            analyzer.analyze_single("This is a test.")
            logger.info("Model warmup completed")
    except Exception as e:
        logger.warning(f"Model warmup failed: {str(e)}")

    logger.info("SentimentSense service startup completed")

    yield

    # Shutdown
    logger.info("Shutting down SentimentSense service...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add monitoring middleware
if settings.ENABLE_METRICS:
    app.middleware("http")(metrics_middleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Should restrict to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc),
            code="INTERNAL_ERROR"
        ).dict()
    )


@app.get("/", response_model=dict)
async def root():
    """Root path - service information"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=OverallHealth)
async def health_check():
    """Enhanced health check endpoint"""
    try:
        health_result = await health_checker.check_all()

        # Log health check results
        logger.info(
            "Health check completed",
            extra={
                "status": health_result.status,
                "components": len(health_result.components),
                "uptime": health_result.uptime
            }
        )

        return health_result

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health check failed"
        )


@app.get("/health/simple", response_model=HealthResponse)
async def simple_health_check():
    """Simple health check endpoint (backward compatible)"""
    uptime = time.time() - app_start_time

    return HealthResponse(
        status="healthy" if analyzer.is_healthy() else "unhealthy",
        model_loaded=analyzer.model_loaded,
        version=settings.APP_VERSION,
        uptime=uptime
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if not settings.ENABLE_METRICS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metrics disabled"
        )
    return await get_metrics_endpoint()


@app.post("/analyze", response_model=SentimentResponse)
async def analyze_sentiment(request: SentimentRequest):
    """
    Analyze sentiment of a single text

    - **text**: English text to analyze (1-512 characters)

    Returns sentiment label (POSITIVE/NEGATIVE) and confidence score
    """
    request_id = str(uuid.uuid4())[:8]

    logger.info(
        "Received sentiment analysis request",
        extra={
            "request_id": request_id,
            "text_length": len(request.text),
            "endpoint": "/analyze"
        }
    )

    try:
        if not analyzer.is_healthy():
            metrics_collector.record_error("ServiceUnavailable", "/analyze")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Sentiment analysis service unavailable"
            )

        start_time = time.time()
        sentiment, confidence, processing_time = analyzer.analyze_single(request.text)

        # Record model inference metrics
        if settings.ENABLE_METRICS:
            metrics_collector.record_model_inference(
                model_name=settings.MODEL_NAME,
                sentiment=sentiment,
                duration=processing_time
            )

        logger.info(
            "Sentiment analysis completed",
            extra={
                "request_id": request_id,
                "sentiment": sentiment,
                "confidence": confidence,
                "processing_time": processing_time
            }
        )

        return SentimentResponse(
            text=request.text,
            sentiment=sentiment,
            confidence=confidence,
            processing_time=processing_time
        )

    except HTTPException:
        raise
    except Exception as e:
        metrics_collector.record_error(type(e).__name__, "/analyze")
        logger.error(
            "Sentiment analysis failed",
            extra={
                "request_id": request_id,
                "error": str(e),
                "error_type": type(e).__name__
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sentiment analysis failed: {str(e)}"
        )


@app.post("/analyze/batch", response_model=BatchSentimentResponse)
async def analyze_batch_sentiment(request: BatchSentimentRequest):
    """
    Batch analyze text sentiment

    - **texts**: List of English texts to analyze (max 10 texts, 1-512 characters each)

    Returns sentiment analysis results for each text
    """
    try:
        if not analyzer.is_healthy():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Sentiment analysis service unavailable"
            )
        
        start_time = time.time()
        batch_results = analyzer.analyze_batch(request.texts)
        total_processing_time = time.time() - start_time
        
        results = []
        for i, (sentiment, confidence, processing_time) in enumerate(batch_results):
            results.append(SentimentResponse(
                text=request.texts[i],
                sentiment=sentiment,
                confidence=confidence,
                processing_time=processing_time
            ))
        
        return BatchSentimentResponse(
            results=results,
            total_count=len(results),
            total_processing_time=total_processing_time
        )
        
    except Exception as e:
        logger.error(f"批量情感分析失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch sentiment analysis failed: {str(e)}"
        )


if __name__ == "__main__":
    # Development environment run
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
