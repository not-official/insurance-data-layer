from __future__ import annotations

import hashlib
import json
import re
from abc import ABC, abstractmethod
from typing import Any

from insurance_data_layer.models import CanonicalRecord


def stable_key(prefix: str, value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()
    return f"{prefix}_{hashlib.sha256(encoded).hexdigest()[:20]}"


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    return cleaned or "unknown"


class SourceAdapter(ABC):
    source_site: str
    adapter_version = "1.0.0"

    @abstractmethod
    def adapt(self, raw: dict[str, Any], raw_file: str) -> CanonicalRecord:
        """Translate one raw source record to the canonical model."""


ADAPTERS: dict[str, type[SourceAdapter]] = {}


def register(adapter: type[SourceAdapter]) -> type[SourceAdapter]:
    ADAPTERS[adapter.source_site] = adapter
    return adapter
