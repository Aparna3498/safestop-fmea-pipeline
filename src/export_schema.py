"""Export or verify the JSON Schema for the FMEA candidate array."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pydantic import TypeAdapter

from .fmea_models import FMEACandidate


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "schemas" / "fmea_candidates.schema.json"


def candidate_schema() -> dict[str, object]:
    """Return the JSON Schema generated from the canonical Pydantic model."""
    schema = TypeAdapter(list[FMEACandidate]).json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["title"] = "SafeStop preliminary FMEA candidate array"
    return schema


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if the committed schema differs from the model",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    expected = candidate_schema()

    if args.check:
        try:
            actual = json.loads(args.output.read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(f"Schema check failed: missing {args.output}")
            return 1
        except json.JSONDecodeError as exc:
            print(f"Schema check failed: invalid JSON: {exc}")
            return 1

        if actual != expected:
            print("Schema check failed: regenerate with python -m src.export_schema")
            return 1

        print("FMEA candidate schema is current")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(expected, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.output.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
