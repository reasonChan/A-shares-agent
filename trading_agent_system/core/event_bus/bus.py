from __future__ import annotations

from collections.abc import Callable
from typing import Protocol


EventHandler = Callable[[object], None]


class EventBus(Protocol):
    def publish(self, topic: str, event: object) -> None:
        ...

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        ...

    def events(self, topic: str) -> list[object]:
        ...
