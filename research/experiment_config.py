from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

import json


@dataclass(frozen=True, slots=True)
class ResearchExperimentConfig:
    experiment_id: str
    description: str
    strategy_version: str = "leadership_expansion_v1"
    version: str = "1"
    creation_timestamp_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    research_notes: str = ""
    component_overrides: dict[str, bool] = field(default_factory=dict)
    expected_baseline: bool = False
    random_seed: int | None = None

    def configuration_hash(self) -> str:
        canonical = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()

    @classmethod
    def from_json(cls, path: Path) -> "ResearchExperimentConfig":
        return cls(**json.loads(path.read_text(encoding="utf-8")))

    def to_manifest(self, **context: Any) -> dict[str, Any]:
        enabled = [name for name, enabled in self.component_overrides.items() if enabled]
        disabled = [name for name, enabled in self.component_overrides.items() if not enabled]
        return {
            **asdict(self),
            "configuration_hash": self.configuration_hash(),
            "enabled_components": enabled,
            "disabled_components": disabled,
            **context,
        }
