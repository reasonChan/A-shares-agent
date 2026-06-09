from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from trading_agent_system.schemas import EVENT_MODEL_BY_TOPIC


class JsonlEventRepository:
    def __init__(self, base_dir: str | Path = "data/events") -> None:
        self.base_dir = Path(base_dir)

    def append(self, topic: str, event: BaseModel | dict[str, Any]) -> None:
        data = event.model_dump(mode="json") if isinstance(event, BaseModel) else event
        path = self._topic_path(topic)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(data, ensure_ascii=False, default=str) + "\n")

    def load(self, topic: str) -> list[object]:
        path = self._topic_path(topic)
        if not path.exists():
            return []
        model = EVENT_MODEL_BY_TOPIC.get(topic)
        loaded: list[object] = []
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                data = json.loads(line)
                loaded.append(model.model_validate(data) if model else data)
        return loaded

    def _topic_path(self, topic: str) -> Path:
        return self.base_dir / f"{topic.replace('.', '_')}.jsonl"
