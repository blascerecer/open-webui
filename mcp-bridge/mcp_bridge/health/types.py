from pydantic import BaseModel, Field
from typing import Literal, Optional
import datetime


class UnhealthyEvent(BaseModel):
    """Represents an unhealthy event"""

    name: str = Field(..., description="Name of the event")
    severity: Literal["error", "warning"] = Field(
        ..., description="Severity of the event"
    )
    traceback: Optional[str] = Field(default=None, description="Traceback of the error")
    timestamp: str = Field(
        default_factory=lambda: datetime.datetime.now().isoformat(),
        description="Time of the event",
    )


class HealthCheckResponse(BaseModel):
    """Represents a health check response"""

    status: Literal["ok", "error"] = Field(..., description="Server status")
    unhealthy_events: list[UnhealthyEvent] = Field(
        default_factory=list, description="List of unhealthy events"
    )
