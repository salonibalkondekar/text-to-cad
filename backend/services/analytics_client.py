"""
Client for interacting with the analytics service
"""

import os
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

from core.config import settings


class AnalyticsClient:
    """Client for analytics service API"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("ANALYTICS_URL", "http://analytics:8001")
        self.client = httpx.Client(timeout=30.0)

    async def create_session(
        self, email: str, name: str, request_headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Create a new session in analytics service"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/create-session",
                data={"email": email, "name": name},
                headers={
                    "User-Agent": request_headers.get("user-agent", ""),
                    "X-Forwarded-For": request_headers.get("x-forwarded-for", ""),
                },
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information from analytics service"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/users/{user_id}/info")
            response.raise_for_status()
            return response.json()

    async def increment_user_count(
        self, user_id: str, session_cookie: str
    ) -> Dict[str, Any]:
        """Increment user's model count"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/users/increment-count",
                params={"user_id": user_id},
                headers={"Cookie": f"session_id={session_cookie}"},
            )
            response.raise_for_status()
            return response.json()

    async def track_cad_event(
        self, session_cookie: str, event_data: Dict[str, Any]
    ) -> None:
        """Track a CAD generation event"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/track/cad-event",
                json=event_data,
                headers={"Cookie": f"session_id={session_cookie}"},
            )
            response.raise_for_status()

    async def store_model(
        self, session_cookie: str, model_data: Dict[str, Any]
    ) -> None:
        """Store a generated model with metadata"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/models/store",
                json=model_data,
                headers={"Cookie": f"session_id={session_cookie}"},
            )
            response.raise_for_status()

    async def track_model_download(self, model_id: str) -> None:
        """Track when a model is downloaded"""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/models/{model_id}/download")
            response.raise_for_status()

    def close(self):
        """Close the client"""
        self.client.close()


# Global analytics client instance
analytics_client = AnalyticsClient()
