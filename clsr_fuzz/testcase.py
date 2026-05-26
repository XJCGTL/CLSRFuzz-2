from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class TestCase:
    instructions: List[str]
    memory_map: Dict[str, Any] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "TestCase":
        return TestCase(
            instructions=list(data.get("instructions", [])),
            memory_map=dict(data.get("memory_map", {})),
            params=dict(data.get("params", {})),
            metadata=dict(data.get("metadata", {})),
        )

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, indent=2)

    @staticmethod
    def load(path: str | Path) -> "TestCase":
        with Path(path).open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return TestCase.from_dict(data)
