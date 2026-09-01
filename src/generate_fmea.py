"""Generate preliminary FMEA candidates from the repository evidence."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import yaml

from .fmea_models import FMEAResponse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
PROMPT_PATH = PROJECT_ROOT / "prompts" / "fmea_prompt.md"
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")
TRIAL_IDS = ("TRIAL-01", "TRIAL-02", "TRIAL-03")


def load_yaml(path: Path) -> object:
    """Load YAML while producing a useful error for the command line."""
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Missing input file: {path.relative_to(PROJECT_ROOT)}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path.relative_to(PROJECT_ROOT)}: {exc}") from exc


def build_evidence_package() -> str:
    """Serialize only the approved repository inputs for the model."""
    evidence = {
        "system_definition": load_yaml(DATA_DIR / "system.yaml"),
        "assumptions_register": load_yaml(DATA_DIR / "assumptions.yaml"),
        "safety_requirements": load_yaml(DATA_DIR / "requirements.yaml"),
    }
    return yaml.safe_dump(evidence, sort_keys=False, allow_unicode=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial-id", choices=TRIAL_IDS, default="TRIAL-01")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "outputs",
        help="Parent directory for trial artifacts",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the prompt package without calling the API",
    )
    return parser.parse_args()


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    trial_dir = args.output_dir / args.trial_id
    trial_dir.mkdir(parents=True, exist_ok=True)

    try:
        instructions = PROMPT_PATH.read_text(encoding="utf-8")
        evidence = build_evidence_package()
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1

    if args.dry_run:
        preview = trial_dir / "prompt_preview.txt"
        preview.write_text(
            f"{instructions}\n\n===== BEGIN SUPPLIED EVIDENCE =====\n"
            f"{evidence}===== END SUPPLIED EVIDENCE =====\n",
            encoding="utf-8",
        )
        print(f"Dry run passed; wrote {preview.relative_to(PROJECT_ROOT)}")
        return 0

    if not os.getenv("OPENAI_API_KEY"):
        print(
            "ERROR: OPENAI_API_KEY is not set. Add it as a GitHub Actions "
            "repository secret or run with --dry-run."
        )
        return 1

    # Imported only for a real generation run, so dry-run validation does not
    # require network access or API credentials.
    from openai import OpenAI

    client = OpenAI()
    try:
        response = client.responses.parse(
            model=args.model,
            input=[
                {"role": "system", "content": instructions},
                {
                    "role": "user",
                    "content": (
                        "Generate the preliminary FMEA candidates using only the "
                        "supplied evidence below.\n\n"
                        "===== BEGIN SUPPLIED EVIDENCE =====\n"
                        f"{evidence}"
                        "===== END SUPPLIED EVIDENCE ====="
                    ),
                },
            ],
            text_format=FMEAResponse,
        )
    except Exception as exc:  # The SDK exposes several API-specific subclasses.
        print(f"ERROR: OpenAI generation failed: {exc}")
        return 1

    parsed = response.output_parsed
    if parsed is None:
        print("ERROR: The model did not return a parsed FMEA response")
        return 1

    candidates_path = trial_dir / "fmea_candidates.json"
    metadata_path = trial_dir / "run_metadata.json"
    candidates = [item.model_dump(mode="json") for item in parsed.candidates]
    write_json(candidates_path, candidates)
    write_json(
        metadata_path,
        {
            "trial_id": args.trial_id,
            "model": args.model,
            "response_id": response.id,
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "human_review_required": True,
            "acceptance_evidence": False,
        },
    )

    print(f"Generated {len(candidates)} candidates")
    print(f"- Candidates: {candidates_path.relative_to(PROJECT_ROOT)}")
    print(f"- Metadata: {metadata_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
