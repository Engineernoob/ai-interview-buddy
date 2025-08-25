"""
Security and utility middleware for AI Interview Buddy.
"""

import time
import logging
from typing import Dict, List
from fastapi import Request, Response
# Fix: Updated import path for FastAPI middleware
from starlette.middleware.base import BaseHTTPMiddleware
from utils.config import get_config

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    def __init__(self, app):
        super().__init__(app)
        self.config = get_config()
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": self._get_csp_header(),
        }
        
        # Only add HSTS in production with HTTPS
        if self.config.environment.value == "production":
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response
    
    def _get_csp_header(self) -> str:
        """Generate Content Security Policy header based on environment."""
        base_csp = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",  # Next.js requires unsafe-inline
            "style-src 'self' 'unsafe-inline'",   # Tailwind requires unsafe-inline
            "img-src 'self' data: blob:",
            "font-src 'self'",
            "connect-src 'self'",
            "media-src 'self' blob:",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'"
        ]
        
        # Allow WebSocket connections
        if self.config.environment.value == "development":
            base_csp.append("connect-src 'self' ws://localhost:* http://localhost:*")
        else:
            base_csp.append("connect-src 'self' wss:")
        
        return "; ".join(base_csp)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log incoming requests and responses."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent", "")
            }
        )
        
        response = await call_next(request)
        
        # Calculate response time
        process_time = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response {response.status_code} - {process_time:.3f}s",
            extra={
                "status_code": response.status_code,
                "process_time": process_time,
                "method": request.method,
                "path": request.url.path
            }
        )
        
        # Add response time header
        response.headers["X-Process-Time"] = str(round(process_time, 3))
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(self, app):
        super().__init__(app)
        self.config = get_config()
        self.request_counts: Dict[str, List[float]] = {}
        self.window_size = 60  # 1 minute window
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old requests
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                req_time for req_time in self.request_counts[client_ip]
                if current_time - req_time < self.window_size
            ]
        else:
            self.request_counts[client_ip] = []
        
        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.config.security.rate_limit_requests:
            logger.warning(
                f"Rate limit exceeded for IP: {client_ip}",
                extra={"client_ip": client_ip, "request_count": len(self.request_counts[client_ip])}
            )
            return Response(
                content='{"error": {"message": "Rate limit exceeded", "code": "RATE_LIMIT_EXCEEDED"}}',
                status_code=429,
                headers={"Content-Type": "application/json"}
            )
        
        # Add current request
        self.request_counts[client_ip].append(current_time)
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.config.security.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.config.security.rate_limit_requests - len(self.request_counts[client_ip]))
        )
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address, considering proxies."""
        # Check for forwarded headers (in case of reverse proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        forwarded = request.headers.get("x-forwarded")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add appropriate cache control headers."""
    
    def __init__(self, app):
        super().__init__(app)
        self.static_paths = ["/static", "/assets", "/favicon.ico", "/manifest.json"]
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        path = request.url.path
        
        # Static assets - cache for a longer time
        if any(path.startswith(static_path) for static_path in self.static_paths):
            response.headers["Cache-Control"] = "public, max-age=31536000"  # 1 year
        
        # API endpoints - no cache
        elif path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        # Health and config endpoints - short cache
        elif path in ["/health", "/config"]:
            response.headers["Cache-Control"] = "public, max-age=60"  # 1 minute
        
        # Default - no cache for dynamic content
        else:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response