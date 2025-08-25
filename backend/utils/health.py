"""
Health check utilities for AI Interview Buddy services.
"""

import asyncio
import logging
import time
import aiohttp
import psutil
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

from utils.config import get_config, AppConfig

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status values."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheck:
    """Individual health check result."""
    
    def __init__(
        self,
        name: str,
        status: HealthStatus,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        response_time_ms: Optional[float] = None
    ):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.response_time_ms = response_time_ms
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        result = {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }
        
        if self.response_time_ms is not None:
            result["response_time_ms"] = self.response_time_ms
        
        if self.details:
            result["details"] = self.details
        
        return result


class HealthChecker:
    """Health check coordinator."""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.start_time = datetime.utcnow()
        self.check_cache: Dict[str, HealthCheck] = {}
        self.cache_ttl = timedelta(seconds=30)  # Cache results for 30 seconds
    
    async def check_all(self, include_details: bool = False) -> Dict[str, Any]:
        """Run all health checks and return aggregated results."""
        checks = await asyncio.gather(
            self.check_system_resources(),
            self.check_whisper_service(),
            self.check_llm_service(),
            self.check_ollama_service() if self.config.llm.use_local else self.check_openai_service(),
            return_exceptions=True
        )
        
        # Filter out exceptions and convert to HealthCheck objects
        health_checks = [check for check in checks if isinstance(check, HealthCheck)]
        
        # Determine overall status
        overall_status = self._determine_overall_status(health_checks)
        
        # Calculate uptime
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
        
        result = {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": uptime_seconds,
            "version": "1.0.0",
            "environment": self.config.environment.value,
            "checks": {check.name: check.to_dict() for check in health_checks}
        }
        
        if include_details:
            result["system"] = self._get_system_info()
            result["config"] = self._get_config_summary()
        
        return result
    
    def _determine_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Determine overall system status from individual checks."""
        if not checks:
            return HealthStatus.UNKNOWN
        
        statuses = [check.status for check in checks]
        
        if any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in statuses):
            return HealthStatus.DEGRADED
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    async def check_system_resources(self) -> HealthCheck:
        """Check system resource usage."""
        try:
            start_time = time.time()
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine status based on resource usage
            status = HealthStatus.HEALTHY
            issues = []
            
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 70:
                status = HealthStatus.DEGRADED
                issues.append(f"Elevated CPU usage: {cpu_percent:.1f}%")
            
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            elif memory.percent > 70:
                status = HealthStatus.DEGRADED
                issues.append(f"Elevated memory usage: {memory.percent:.1f}%")
            
            if disk.percent > 90:
                status = HealthStatus.UNHEALTHY
                issues.append(f"High disk usage: {disk.percent:.1f}%")
            elif disk.percent > 80:
                status = HealthStatus.DEGRADED
                issues.append(f"Elevated disk usage: {disk.percent:.1f}%")
            
            message = "; ".join(issues) if issues else "System resources are healthy"
            
            return HealthCheck(
                name="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_percent": round(cpu_percent, 1),
                    "memory_percent": round(memory.percent, 1),
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": round(disk.percent, 1),
                    "disk_free_gb": round(disk.free / (1024**3), 2)
                },
                response_time_ms=round(response_time, 2)
            )
        
        except Exception as e:
            logger.error(f"System resources check failed: {e}")
            return HealthCheck(
                name="system_resources",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check system resources: {str(e)}"
            )
    
    async def check_whisper_service(self) -> HealthCheck:
        """Check Whisper transcription service."""
        try:
            start_time = time.time()
            
            # Try to import and initialize Whisper
            from faster_whisper import WhisperModel
            
            # This is a lightweight check - just verify the model can be loaded
            model_path = self.config.whisper.model
            model = WhisperModel(model_path, device="cpu")
            
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheck(
                name="whisper_service",
                status=HealthStatus.HEALTHY,
                message="Whisper service is operational",
                details={
                    "model": model_path,
                    "device": "cpu"
                },
                response_time_ms=round(response_time, 2)
            )
        
        except ImportError:
            return HealthCheck(
                name="whisper_service",
                status=HealthStatus.UNHEALTHY,
                message="Whisper dependencies not installed"
            )
        except Exception as e:
            logger.error(f"Whisper service check failed: {e}")
            return HealthCheck(
                name="whisper_service",
                status=HealthStatus.DEGRADED,
                message=f"Whisper service check failed: {str(e)}"
            )
    
    async def check_llm_service(self) -> HealthCheck:
        """Check LLM service availability."""
        if self.config.llm.use_local:
            return await self.check_ollama_service()
        else:
            return await self.check_openai_service()
    
    async def check_ollama_service(self) -> HealthCheck:
        """Check Ollama local LLM service."""
        try:
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.llm.ollama_url}/api/version",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        version_data = await response.json()
                        response_time = (time.time() - start_time) * 1000
                        
                        return HealthCheck(
                            name="ollama_service",
                            status=HealthStatus.HEALTHY,
                            message="Ollama service is running",
                            details={
                                "url": self.config.llm.ollama_url,
                                "model": self.config.llm.model_name,
                                "version": version_data.get("version", "unknown")
                            },
                            response_time_ms=round(response_time, 2)
                        )
                    else:
                        return HealthCheck(
                            name="ollama_service",
                            status=HealthStatus.UNHEALTHY,
                            message=f"Ollama service returned status {response.status}"
                        )
        
        except asyncio.TimeoutError:
            return HealthCheck(
                name="ollama_service",
                status=HealthStatus.UNHEALTHY,
                message="Ollama service timeout"
            )
        except Exception as e:
            logger.error(f"Ollama service check failed: {e}")
            return HealthCheck(
                name="ollama_service",
                status=HealthStatus.UNHEALTHY,
                message=f"Cannot connect to Ollama service: {str(e)}"
            )
    
    async def check_openai_service(self) -> HealthCheck:
        """Check OpenAI API service."""
        try:
            if not self.config.openai.api_key:
                return HealthCheck(
                    name="openai_service",
                    status=HealthStatus.UNHEALTHY,
                    message="OpenAI API key not configured"
                )
            
            start_time = time.time()
            
            headers = {
                "Authorization": f"Bearer {self.config.openai.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.openai.com/v1/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return HealthCheck(
                            name="openai_service",
                            status=HealthStatus.HEALTHY,
                            message="OpenAI API is accessible",
                            details={
                                "model": self.config.openai.model
                            },
                            response_time_ms=round(response_time, 2)
                        )
                    elif response.status == 401:
                        return HealthCheck(
                            name="openai_service",
                            status=HealthStatus.UNHEALTHY,
                            message="OpenAI API key is invalid"
                        )
                    else:
                        return HealthCheck(
                            name="openai_service",
                            status=HealthStatus.DEGRADED,
                            message=f"OpenAI API returned status {response.status}"
                        )
        
        except asyncio.TimeoutError:
            return HealthCheck(
                name="openai_service",
                status=HealthStatus.DEGRADED,
                message="OpenAI API timeout"
            )
        except Exception as e:
            logger.error(f"OpenAI service check failed: {e}")
            return HealthCheck(
                name="openai_service",
                status=HealthStatus.DEGRADED,
                message=f"Cannot connect to OpenAI API: {str(e)}"
            )
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get basic system information."""
        try:
            return {
                "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
                "cpu_count": psutil.cpu_count(),
                "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                "platform": psutil.os.name,
                "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {"error": "Unable to retrieve system information"}
    
    def _get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary (without sensitive data)."""
        return {
            "environment": self.config.environment.value,
            "debug": self.config.debug,
            "whisper_model": self.config.whisper.model,
            "use_local_llm": self.config.llm.use_local,
            "llm_model": self.config.llm.model_name if self.config.llm.use_local else self.config.openai.model,
            "max_file_size_mb": round(self.config.security.max_file_size / (1024**2), 1)
        }


# Global health checker instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker(get_config())
    return _health_checker