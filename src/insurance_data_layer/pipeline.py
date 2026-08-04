from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from insurance_data_layer.adapters import ADAPTERS
from insurance_data_layer.models import CanonicalRecord


def normalize_raw_file_path(path: Path) -> str:
    """Store file paths consistently with forward slashes on every OS."""
    return path.as_posix()


def load_raw(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, list):
        raise TypeError(f"Expected a JSON array in {path}")

    return data


def transform_file(path: Path) -> tuple[list[CanonicalRecord], dict[str, Any]]:
    records: list[CanonicalRecord] = []
    errors: list[dict[str, Any]] = []
    normalized_raw_file = normalize_raw_file_path(path)

    for index, raw in enumerate(load_raw(path)):
        try:
            source_site = raw["output"]["source_site"]
            adapter_type = ADAPTERS.get(source_site)

            if adapter_type is None:
                raise ValueError(
                    f"No adapter registered for source_site={source_site!r}"
                )

            records.append(
                adapter_type().adapt(
                    raw,
                    raw_file=normalized_raw_file,
                )
            )
        except Exception as exc:  # noqa: BLE001 - quarantine malformed records
            errors.append(
                {
                    "index": index,
                    "error": str(exc),
                }
            )

    report = {
        "raw_file": normalized_raw_file,
        "input_records": len(records) + len(errors),
        "valid_records": len(records),
        "invalid_records": len(errors),
        "unique_quote_requests": len(
            {
                record.quote_request.request_key
                for record in records
            }
        ),
        "providers": dict(
            Counter(
                record.provider.code
                for record in records
            )
        ),
        "insurance_types": dict(
            Counter(
                record.product.insurance_type.value
                for record in records
            )
        ),
        "quality_issue_counts": dict(
            Counter(
                issue.code
                for record in records
                for issue in record.quality_issues
            )
        ),
        "errors": errors,
    }

    return records, report


def write_jsonl(
    records: list[CanonicalRecord],
    destination: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json() + "\n")