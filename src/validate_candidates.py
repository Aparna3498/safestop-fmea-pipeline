"""Validate generated FMEA candidates structurally and semantically."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml
from pydantic import TypeAdapter, ValidationError

from .fmea_models import FMEACandidate


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CANDIDATE_ADAPTER = TypeAdapter(list[FMEACandidate])
PROHIBITED_CLAIM_PATTERNS = (
    re.compile(r"\bSIL\s*[0-9]", re.IGNORECASE),
    re.compile(r"\bPL\s*[a-e]\b", re.IGNORECASE),
    re.compile(r"\b(?:is|are|design is)\s+certified\b", re.IGNORECASE),
    re.compile(r"\b(?:complies|compliant)\s+with\b", re.IGNORECASE),
)


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Missing candidate file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def load_yaml_mapping(path: Path) -> dict[str, object]:
    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Missing evidence file: {path}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(content, dict):
        raise ValueError(f"Evidence root must be a mapping: {path}")
    return content


def evidence_id_sets() -> tuple[set[str], set[str]]:
    """Return allowed boundary IDs and all IDs that can be cited."""
    system = load_yaml_mapping(DATA_DIR / "system.yaml")
    assumptions = load_yaml_mapping(DATA_DIR / "assumptions.yaml")
    requirements = load_yaml_mapping(DATA_DIR / "requirements.yaml")

    boundary_ids: set[str] = set()
    system_ids: set[str] = set()

    project = system.get("project", {})
    if isinstance(project, dict) and project.get("id"):
        system_ids.add(str(project["id"]))

    safety_function = system.get("safety_function", {})
    if isinstance(safety_function, dict) and safety_function.get("id"):
        system_ids.add(str(safety_function["id"]))

    elements = system.get("elements", [])
    if isinstance(elements, list):
        for element in elements:
            if not isinstance(element, dict):
                continue
            if element.get("id"):
                element_id = str(element["id"])
                boundary_ids.add(element_id)
                system_ids.add(element_id)
            interfaces = element.get("interfaces", [])
            if isinstance(interfaces, list):
                for interface in interfaces:
                    interface_id = str(interface)
                    boundary_ids.add(interface_id)
                    system_ids.add(interface_id)

    assumption_ids = {
        str(row["id"])
        for row in assumptions.get("assumptions", [])
        if isinstance(row, dict) and row.get("id")
    }
    requirement_ids = {
        str(row["id"])
        for row in requirements.get("requirements", [])
        if isinstance(row, dict) and row.get("id")
    }
    return boundary_ids, system_ids | assumption_ids | requirement_ids


def candidate_text(candidate: FMEACandidate) -> str:
    """Combine narrative fields for prohibited-claim screening."""
    return " ".join(
        [
            candidate.failure_mode,
            candidate.local_effect,
            candidate.system_effect,
            candidate.hazardous_consequence,
            candidate.detection_mechanism,
            candidate.recommended_action,
            *candidate.assumptions,
            *candidate.missing_information,
        ]
    )


def semantic_errors(
    candidates: list[FMEACandidate],
    boundary_ids: set[str],
    allowed_evidence_ids: set[str],
) -> list[str]:
    """Apply checks that are stricter than the JSON data types."""
    errors: list[str] = []
    seen_mechanisms: set[tuple[str, str]] = set()

    for index, candidate in enumerate(candidates, start=1):
        expected_id = f"AI-{index:03d}"
        if candidate.candidate_id != expected_id:
            errors.append(
                f"{candidate.candidate_id}: expected sequential ID {expected_id}"
            )

        if candidate.element_id not in boundary_ids:
            errors.append(
                f"{candidate.candidate_id}: element_id '{candidate.element_id}' "
                "is outside the supplied boundary"
            )

        unknown_references = sorted(
            set(candidate.evidence_references) - allowed_evidence_ids
        )
        for reference in unknown_references:
            errors.append(
                f"{candidate.candidate_id}: unknown evidence reference '{reference}'"
            )

        if not any(
            reference.startswith(("A-", "SR-"))
            for reference in candidate.evidence_references
        ):
            errors.append(
                f"{candidate.candidate_id}: cite at least one assumption or requirement ID"
            )

        mechanism_key = (
            candidate.element_id.casefold(),
            " ".join(candidate.failure_mode.casefold().split()),
        )
        if mechanism_key in seen_mechanisms:
            errors.append(
                f"{candidate.candidate_id}: duplicate element/failure-mode mechanism"
            )
        seen_mechanisms.add(mechanism_key)

        text = candidate_text(candidate)
        if any(pattern.search(text) for pattern in PROHIBITED_CLAIM_PATTERNS):
            errors.append(
                f"{candidate.candidate_id}: contains a prohibited SIL, PL, "
                "certification or compliance claim"
            )

    return errors


def validate_candidate_file(path: Path) -> tuple[list[FMEACandidate], list[str]]:
    """Load and validate one generated candidate array."""
    try:
        payload = load_json(path)
        candidates = CANDIDATE_ADAPTER.validate_python(payload)
        boundary_ids, allowed_evidence_ids = evidence_id_sets()
    except (ValueError, ValidationError) as exc:
        return [], [str(exc)]

    return candidates, semantic_errors(candidates, boundary_ids, allowed_evidence_ids)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_file", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates, errors = validate_candidate_file(args.candidate_file)

    if errors:
        print("Candidate validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Candidate validation passed: {len(candidates)} candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
