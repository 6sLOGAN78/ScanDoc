"""
Application Layer Event Bus for scanDOC TUI and multi-interface event distribution.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class EventType(str, Enum):
    DOCUMENT_IMPORTED = "document.imported"
    PROCESSING_STARTED = "processing.started"
    STAGE_STARTED = "stage.started"
    STAGE_COMPLETED = "stage.completed"
    PROCESSING_COMPLETED = "processing.completed"
    PROCESSING_FAILED = "processing.failed"
    JOB_STATUS_CHANGED = "job.status_changed"
    MODEL_STATUS_CHANGED = "model.status_changed"
    LOG_EMITTED = "log.emitted"
    SERVER_STATUS_CHANGED = "server.status_changed"


@dataclass
class AppEvent:
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    payload: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None


class EventBus:
    """
    Decoupled Event Bus enabling core engine events to update application state,
    job manager, logging infrastructure, and presentation layers without circular dependencies.
    """

    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable[[AppEvent], None]]] = {}

    def subscribe(self, event_type: EventType, callback: Callable[[AppEvent], None]) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def publish(self, event: AppEvent) -> None:
        callbacks = self._subscribers.get(event.event_type, [])
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                pass


default_event_bus = EventBus()
