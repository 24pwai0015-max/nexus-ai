import time
from typing import Dict, Any
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings

security = HTTPBearer(auto_error=False)

class AuthService:
    def __init__(self):
        # In-memory usage telemetry
        self.usage_stats: Dict[str, Any] = {
            "total_requests": 0,
            "requests_by_endpoint": {},
            "requests_by_key": {},
            "start_time": time.time()
        }

    def verify_api_key(self, credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
        """
        Validates Bearer token against registered Nexus API keys.
        """
        if not credentials or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Provide header 'Authorization: Bearer <YOUR_NEXUS_API_KEY>'",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = credentials.credentials.strip()
        if token not in settings.valid_api_keys:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Invalid Nexus API Key.",
            )

        return token

    def record_usage(self, api_key: str, endpoint: str):
        """
        Records API usage metrics for monitoring and quota accounting.
        """
        self.usage_stats["total_requests"] += 1
        self.usage_stats["requests_by_endpoint"][endpoint] = (
            self.usage_stats["requests_by_endpoint"].get(endpoint, 0) + 1
        )
        # Obfuscate key for privacy
        masked_key = api_key[:8] + "..." if len(api_key) > 8 else api_key
        self.usage_stats["requests_by_key"][masked_key] = (
            self.usage_stats["requests_by_key"].get(masked_key, 0) + 1
        )

    def get_metrics(self) -> Dict[str, Any]:
        uptime_seconds = int(time.time() - self.usage_stats["start_time"])
        return {
            "total_requests": self.usage_stats["total_requests"],
            "uptime_seconds": uptime_seconds,
            "requests_by_endpoint": self.usage_stats["requests_by_endpoint"],
            "active_keys_count": len(self.usage_stats["requests_by_key"]),
        }

auth_service = AuthService()
