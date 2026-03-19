from pydantic import BaseModel
from typing import Dict, Any
from enum import Enum


class DatabaseStatus(str, Enum):
    healthy = "healthy"
    unhealthy = "unhealthy"


class HealthResponse(BaseModel):
    status: str
    version: str
    database: DatabaseStatus
    services: Dict[str, Any]