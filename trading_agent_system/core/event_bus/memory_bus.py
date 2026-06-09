from __future__ import annotations

from collections import defaultdict

from .bus import EventHandler


class MemoryEventBus:
    def __init__(self) -> None:
        self._events: dict[str, list[object]] = defaultdict(list)
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def publish(self, topic: str, event: object) -> None:
        self._events[topic].append(event)
        for handler in list(self._handlers.get(topic, [])):
            handler(event)

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        self._handlers[topic].append(handler)

    def events(self, topic: str) -> list[object]:
        return list(self._events.get(topic, []))

    def all_events(self) -> dict[str, list[object]]:
        return {topic: list(events) for topic, events in self._events.items()}
