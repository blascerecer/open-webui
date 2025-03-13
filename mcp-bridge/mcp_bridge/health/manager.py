from collections import deque
from .types import UnhealthyEvent

__all__ = ["manager"]


class HealthManager:
    """Manages the health of the server"""

    UnhealthyEvents: deque[UnhealthyEvent] = deque(
        maxlen=100
    )  # we do not want to memory leak

    def add_unhealthy_event(self, event: UnhealthyEvent) -> None:
        self.UnhealthyEvents.append(event)

    def get_unhealthy_events(self) -> list[UnhealthyEvent]:
        return list(self.UnhealthyEvents)

    def is_healthy(self) -> bool:
        return not any(event.severity == "error" for event in self.UnhealthyEvents)


manager: HealthManager = HealthManager()
