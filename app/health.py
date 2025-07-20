"""
Enhanced health check module
"""
import time
import asyncio
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel

from .config import settings
from .logging_config import get_logger
from .metrics import get_health_metrics

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Component health status"""
    name: str
    status: HealthStatus
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    response_time: Optional[float] = None


class OverallHealth(BaseModel):
    """Overall health status"""
    status: HealthStatus
    timestamp: str
    version: str
    uptime: float
    components: List[ComponentHealth]
    metrics: Optional[Dict[str, Any]] = None


class HealthChecker:
    """Health checker"""
    
    def __init__(self):
        self.start_time = time.time()
        self.checks = {
            'model': self._check_model,
            'memory': self._check_memory,
            'disk': self._check_disk,
            'dependencies': self._check_dependencies
        }
    
    async def _check_model(self) -> ComponentHealth:
        """Check model status"""
        start_time = time.time()

        try:
            from .sentiment import analyzer

            if not analyzer.is_healthy():
                return ComponentHealth(
                    name="model",
                    status=HealthStatus.UNHEALTHY,
                    message="Model not loaded or not healthy",
                    response_time=time.time() - start_time
                )

            # Try to execute a simple inference test
            try:
                test_result = analyzer.analyze_single("test")
                if test_result:
                    return ComponentHealth(
                        name="model",
                        status=HealthStatus.HEALTHY,
                        message="Model is loaded and functional",
                        details={
                            "model_name": settings.MODEL_NAME,
                            "model_loaded": analyzer.model_loaded
                        },
                        response_time=time.time() - start_time
                    )
            except Exception as e:
                return ComponentHealth(
                    name="model",
                    status=HealthStatus.DEGRADED,
                    message=f"Model loaded but inference failed: {str(e)}",
                    response_time=time.time() - start_time
                )
                
        except Exception as e:
            return ComponentHealth(
                name="model",
                status=HealthStatus.UNHEALTHY,
                message=f"Model check failed: {str(e)}",
                response_time=time.time() - start_time
            )
    
    async def _check_memory(self) -> ComponentHealth:
        """Check memory usage"""
        start_time = time.time()

        try:
            import psutil
            memory = psutil.virtual_memory()

            # Memory usage thresholds
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"High memory usage: {memory.percent:.1f}%"
            elif memory.percent > 80:
                status = HealthStatus.DEGRADED
                message = f"Elevated memory usage: {memory.percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {memory.percent:.1f}%"
            
            return ComponentHealth(
                name="memory",
                status=status,
                message=message,
                details={
                    "total": memory.total,
                    "used": memory.used,
                    "available": memory.available,
                    "percent": memory.percent
                },
                response_time=time.time() - start_time
            )
            
        except Exception as e:
            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Memory check failed: {str(e)}",
                response_time=time.time() - start_time
            )
    
    async def _check_disk(self) -> ComponentHealth:
        """Check disk usage"""
        start_time = time.time()

        try:
            import psutil
            disk = psutil.disk_usage('/')

            # Disk usage thresholds
            percent = (disk.used / disk.total) * 100
            if percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"High disk usage: {percent:.1f}%"
            elif percent > 80:
                status = HealthStatus.DEGRADED
                message = f"Elevated disk usage: {percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {percent:.1f}%"
            
            return ComponentHealth(
                name="disk",
                status=status,
                message=message,
                details={
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": percent
                },
                response_time=time.time() - start_time
            )
            
        except Exception as e:
            return ComponentHealth(
                name="disk",
                status=HealthStatus.DEGRADED,
                message=f"Disk check failed: {str(e)}",
                response_time=time.time() - start_time
            )
    
    async def _check_dependencies(self) -> ComponentHealth:
        """Check critical dependencies"""
        start_time = time.time()

        try:
            # Check if critical modules can be imported
            critical_modules = [
                'torch',
                'transformers',
                'fastapi',
                'uvicorn'
            ]
            
            missing_modules = []
            for module in critical_modules:
                try:
                    __import__(module)
                except ImportError:
                    missing_modules.append(module)
            
            if missing_modules:
                return ComponentHealth(
                    name="dependencies",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Missing critical modules: {', '.join(missing_modules)}",
                    response_time=time.time() - start_time
                )
            
            return ComponentHealth(
                name="dependencies",
                status=HealthStatus.HEALTHY,
                message="All critical dependencies available",
                details={"modules": critical_modules},
                response_time=time.time() - start_time
            )
            
        except Exception as e:
            return ComponentHealth(
                name="dependencies",
                status=HealthStatus.UNHEALTHY,
                message=f"Dependency check failed: {str(e)}",
                response_time=time.time() - start_time
            )
    
    async def check_all(self) -> OverallHealth:
        """Execute all health checks"""
        components = []

        # Execute all checks in parallel
        tasks = [check() for check in self.checks.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, ComponentHealth):
                components.append(result)
            else:
                # Handle exception cases
                components.append(ComponentHealth(
                    name="unknown",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check failed: {str(result)}"
                ))

        # Determine overall health status
        unhealthy_count = sum(1 for c in components if c.status == HealthStatus.UNHEALTHY)
        degraded_count = sum(1 for c in components if c.status == HealthStatus.DEGRADED)
        
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Get system metrics
        metrics = get_health_metrics()

        return OverallHealth(
            status=overall_status,
            timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            version=settings.APP_VERSION,
            uptime=time.time() - self.start_time,
            components=components,
            metrics=metrics
        )


# Global health checker instance
health_checker = HealthChecker()
