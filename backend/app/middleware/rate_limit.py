import time
from typing import Dict, Tuple
from collections import defaultdict
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

class RateLimitMiddleware:
    """Rate limiting middleware for API endpoints."""
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.coach_limit = "10/minute"  # 10 requests per minute for coaching
        self.run_limit = "30/minute"    # 30 requests per minute for code execution
        self.questions_limit = "100/minute"  # 100 requests per minute for questions
    
    def is_rate_limited(self, key: str, limit: str) -> bool:
        """
        Check if the request is rate limited.
        
        Args:
            key: Unique identifier (usually IP address)
            limit: Rate limit string like "10/minute"
        
        Returns:
            True if rate limited, False otherwise
        """
        
        now = time.time()
        
        # Parse limit string
        limit_parts = limit.split("/")
        max_requests = int(limit_parts[0])
        time_window = self._parse_time_window(limit_parts[1])
        
        # Clean old requests
        cutoff = now - time_window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > cutoff
        ]
        
        # Check if limit exceeded
        if len(self.requests[key]) >= max_requests:
            return True
        
        # Add current request
        self.requests[key].append(now)
        return False
    
    def _parse_time_window(self, window_str: str) -> int:
        """Parse time window string to seconds."""
        
        window_str = window_str.lower()
        
        if window_str == "second":
            return 1
        elif window_str == "minute":
            return 60
        elif window_str == "hour":
            return 3600
        elif window_str == "day":
            return 86400
        else:
            # Handle formats like "1m", "5h", etc.
            import re
            match = re.match(r'(\d+)([smhd])', window_str)
            if match:
                num = int(match.group(1))
                unit = match.group(2)
                
                if unit == 's':
                    return num
                elif unit == 'm':
                    return num * 60
                elif unit == 'h':
                    return num * 3600
                elif unit == 'd':
                    return num * 86400
        
        return 60  # Default to 1 minute
    
    def get_rate_limit_info(self, key: str) -> Dict[str, Any]:
        """Get rate limit information for a key."""
        
        now = time.time()
        
        info = {
            "requests": len(self.requests[key]),
            "window_start": min(self.requests[key]) if self.requests[key] else now,
            "window_end": now
        }
        
        return info

# Rate limiting decorators for specific endpoints
from functools import wraps

def rate_limit(limit_str: str):
    """Decorator for rate limiting specific endpoints."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request object (assuming it's the first argument)
            request = None
            for arg in args:
                if hasattr(arg, 'client'):
                    request = arg
                    break
            
            if request:
                client_ip = get_remote_address(request)
                middleware = RateLimitMiddleware()
                
                if middleware.is_rate_limited(client_ip, limit_str):
                    raise HTTPException(
                        status_code=429,
                        detail=f"Rate limit exceeded. Limit: {limit_str}"
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Specific rate limit configurations
COACH_RATE_LIMIT = "10/minute"
RUN_RATE_LIMIT = "30/minute"
QUESTIONS_RATE_LIMIT = "100/minute"