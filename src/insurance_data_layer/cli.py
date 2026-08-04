from __future__ import annotations

import argparse
import json
from pathlib import Path

from insurance_data_layer.pipeline import transform_file, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Transform raw insurance observations.")
    parser.add_argument("input", type=Path, help="Raw JSON array")
    parser.add_argument("--output", type=Path, required=True, help="Canonical JSONL destination")
    parser.add_argument("--report", type=Path, help="Validation report destination")
    args = parser.parse_args()

    records, report = transform_file(args.input)
    write_jsonl(records, args.output)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["invalid_records"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
