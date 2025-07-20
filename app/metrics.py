"""
Performance metrics monitoring module
"""
import time
import psutil
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.responses import PlainTextResponse

from .config import settings
from .logging_config import get_logger

logger = get_logger(__name__)

# Prometheus metrics definitions
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)

MODEL_INFERENCE_DURATION = Histogram(
    'model_inference_duration_seconds',
    'Model inference duration in seconds',
    ['model_name']
)

MODEL_INFERENCE_COUNT = Counter(
    'model_inference_total',
    'Total model inferences',
    ['model_name', 'sentiment']
)

ERROR_COUNT = Counter(
    'errors_total',
    'Total errors',
    ['error_type', 'endpoint']
)

# System metrics
MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

CPU_USAGE = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)

MODEL_LOADED = Gauge(
    'model_loaded',
    'Whether the model is loaded (1) or not (0)'
)

# Application information
APP_INFO = Info(
    'app_info',
    'Application information'
)

# Initialize application information
APP_INFO.info({
    'name': settings.APP_NAME,
    'version': settings.APP_VERSION,
    'model_name': settings.MODEL_NAME
})


class MetricsCollector:
    """Metrics collector"""

    def __init__(self):
        self.start_time = time.time()
        self._update_system_metrics()

    def _update_system_metrics(self):
        """Update system metrics"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.used)

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)
            
        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record request metrics"""
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_model_inference(self, model_name: str, sentiment: str, duration: float):
        """Record model inference metrics"""
        MODEL_INFERENCE_COUNT.labels(
            model_name=model_name,
            sentiment=sentiment
        ).inc()
        
        MODEL_INFERENCE_DURATION.labels(
            model_name=model_name
        ).observe(duration)
    
    def record_error(self, error_type: str, endpoint: str):
        """Record error metrics"""
        ERROR_COUNT.labels(
            error_type=error_type,
            endpoint=endpoint
        ).inc()
    
    def set_model_status(self, loaded: bool):
        """Set model loading status"""
        MODEL_LOADED.set(1 if loaded else 0)

    def get_metrics(self) -> str:
        """Get all metrics"""
        self._update_system_metrics()
        return generate_latest()


# Global metrics collector
metrics_collector = MetricsCollector()


async def metrics_middleware(request: Request, call_next):
    """Metrics collection middleware"""
    if not settings.ENABLE_METRICS:
        return await call_next(request)
    
    start_time = time.time()
    ACTIVE_REQUESTS.inc()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Record request metrics
        metrics_collector.record_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration=duration
        )

        # Add response time to response headers
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        
        return response
        
    except Exception as e:
        duration = time.time() - start_time
        
        # Record error metrics
        metrics_collector.record_error(
            error_type=type(e).__name__,
            endpoint=request.url.path
        )

        # Record failed request
        metrics_collector.record_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=500,
            duration=duration
        )
        
        raise
    
    finally:
        ACTIVE_REQUESTS.dec()


async def get_metrics_endpoint() -> PlainTextResponse:
    """Prometheus metrics endpoint"""
    return PlainTextResponse(
        metrics_collector.get_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )


def get_health_metrics() -> Dict[str, Any]:
    """Get health check related metrics"""
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent()
        
        return {
            "memory": {
                "total": memory.total,
                "used": memory.used,
                "available": memory.available,
                "percent": memory.percent
            },
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count()
            },
            "uptime": time.time() - metrics_collector.start_time
        }
    except Exception as e:
        logger.error(f"Failed to get health metrics: {e}")
        return {}
