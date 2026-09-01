"""Validate the structured input evidence for the SafeStop AI-FMEA pipeline."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def load_yaml(path: Path) -> dict[str, Any]:
    """Load one YAML file and require a mapping at its root."""
    try:
        with path.open("r", encoding="utf-8") as stream:
            content = yaml.safe_load(stream)
    except FileNotFoundError as exc:
        raise ValueError(f"Missing input file: {path.relative_to(PROJECT_ROOT)}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML in {path.relative_to(PROJECT_ROOT)}: {exc}") from exc

    if not isinstance(content, dict):
        raise ValueError(f"{path.relative_to(PROJECT_ROOT)} must contain a YAML mapping")

    return content


def missing_fields(record: dict[str, Any], required: set[str]) -> list[str]:
    """Return required fields that are absent or blank."""
    return sorted(
        field
        for field in required
        if field not in record or record[field] is None or record[field] == ""
    )


def find_duplicates(values: list[str]) -> list[str]:
    """Return duplicate strings without repeating them in the result."""
    seen: set[str] = set()
    duplicates: set[str] = set()

    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)

    return sorted(duplicates)


def validate_inputs(
    system: dict[str, Any],
    assumptions: dict[str, Any],
    requirements: dict[str, Any],
) -> tuple[list[str], dict[str, int]]:
    """Validate structure, identifiers and requirement traceability."""
    errors: list[str] = []

    project = system.get("project")
    safety_function = system.get("safety_function")
    elements = system.get("elements")
    assumption_rows = assumptions.get("assumptions")
    requirement_rows = requirements.get("requirements")

    if not isinstance(project, dict):
        errors.append("system.yaml: 'project' must be a mapping")
        project = {}

    if not isinstance(safety_function, dict):
        errors.append("system.yaml: 'safety_function' must be a mapping")
        safety_function = {}

    if not isinstance(elements, list) or not elements:
        errors.append("system.yaml: 'elements' must be a non-empty list")
        elements = []

    if not isinstance(assumption_rows, list) or not assumption_rows:
        errors.append("assumptions.yaml: 'assumptions' must be a non-empty list")
        assumption_rows = []

    if not isinstance(requirement_rows, list) or not requirement_rows:
        errors.append("requirements.yaml: 'requirements' must be a non-empty list")
        requirement_rows = []

    project_required = {"id", "name", "equipment", "purpose"}
    function_required = {"id", "description", "initiating_event", "safe_state", "reset_condition"}
    element_required = {"id", "name", "function", "interfaces", "analysis_boundary"}
    assumption_required = {
        "id",
        "area",
        "statement",
        "rationale",
        "validation_source",
        "status",
    }
    requirement_required = {
        "id",
        "requirement",
        "linked_ids",
        "verification_method",
        "acceptance_evidence",
        "status",
        "notes",
    }

    for field in missing_fields(project, project_required):
        errors.append(f"system.yaml project: missing '{field}'")

    for field in missing_fields(safety_function, function_required):
        errors.append(f"system.yaml safety_function: missing '{field}'")

    element_ids: list[str] = []
    interface_ids: set[str] = set()

    for index, element in enumerate(elements, start=1):
        if not isinstance(element, dict):
            errors.append(f"system.yaml element #{index}: must be a mapping")
            continue

        element_id = str(element.get("id", f"element #{index}"))
        element_ids.append(element_id)

        for field in missing_fields(element, element_required):
            errors.append(f"system.yaml {element_id}: missing '{field}'")

        interfaces = element.get("interfaces", [])
        if not isinstance(interfaces, list) or not interfaces:
            errors.append(f"system.yaml {element_id}: 'interfaces' must be a non-empty list")
        else:
            interface_ids.update(str(interface) for interface in interfaces)

    for duplicate in find_duplicates(element_ids):
        errors.append(f"system.yaml: duplicate element ID '{duplicate}'")

    assumption_ids: list[str] = []
    allowed_assumption_statuses = {"confirmed", "to_verify"}

    for index, assumption in enumerate(assumption_rows, start=1):
        if not isinstance(assumption, dict):
            errors.append(f"assumptions.yaml assumption #{index}: must be a mapping")
            continue

        assumption_id = str(assumption.get("id", f"assumption #{index}"))
        assumption_ids.append(assumption_id)

        for field in missing_fields(assumption, assumption_required):
            errors.append(f"assumptions.yaml {assumption_id}: missing '{field}'")

        if not re.fullmatch(r"A-\d{3}", assumption_id):
            errors.append(f"assumptions.yaml: invalid assumption ID '{assumption_id}'")

        if assumption.get("status") not in allowed_assumption_statuses:
            errors.append(
                f"assumptions.yaml {assumption_id}: status must be "
                f"one of {sorted(allowed_assumption_statuses)}"
            )

    for duplicate in find_duplicates(assumption_ids):
        errors.append(f"assumptions.yaml: duplicate assumption ID '{duplicate}'")

    requirement_ids: list[str] = []
    allowed_requirement_statuses = {"draft", "reviewed", "approved", "rejected"}

    known_system_ids = {
        str(project.get("id", "")),
        str(safety_function.get("id", "")),
        *element_ids,
        *interface_ids,
    }
    known_system_ids.discard("")

    for index, requirement in enumerate(requirement_rows, start=1):
        if not isinstance(requirement, dict):
            errors.append(f"requirements.yaml requirement #{index}: must be a mapping")
            continue

        requirement_id = str(requirement.get("id", f"requirement #{index}"))
        requirement_ids.append(requirement_id)

        # Notes may intentionally be blank, so only require the key to exist.
        fields_to_check = requirement_required - {"notes"}
        for field in missing_fields(requirement, fields_to_check):
            errors.append(f"requirements.yaml {requirement_id}: missing '{field}'")

        if "notes" not in requirement:
            errors.append(f"requirements.yaml {requirement_id}: missing 'notes'")

        if not re.fullmatch(r"SR-\d{3}", requirement_id):
            errors.append(f"requirements.yaml: invalid requirement ID '{requirement_id}'")

        linked_ids = requirement.get("linked_ids", [])
        if not isinstance(linked_ids, list) or not linked_ids:
            errors.append(
                f"requirements.yaml {requirement_id}: 'linked_ids' must be a non-empty list"
            )
        else:
            for linked_id in linked_ids:
                if str(linked_id) not in known_system_ids:
                    errors.append(
                        f"requirements.yaml {requirement_id}: unknown linked ID '{linked_id}'"
                    )

        if requirement.get("status") not in allowed_requirement_statuses:
            errors.append(
                f"requirements.yaml {requirement_id}: status must be "
                f"one of {sorted(allowed_requirement_statuses)}"
            )

    for duplicate in find_duplicates(requirement_ids):
        errors.append(f"requirements.yaml: duplicate requirement ID '{duplicate}'")

    metrics = {
        "elements": len(element_ids),
        "interfaces": len(interface_ids),
        "assumptions": len(assumption_ids),
        "requirements": len(requirement_ids),
    }

    return errors, metrics


def main() -> int:
    """Load the repository inputs, validate them and return a CI-friendly exit code."""
    try:
        system = load_yaml(DATA_DIR / "system.yaml")
        assumptions = load_yaml(DATA_DIR / "assumptions.yaml")
        requirements = load_yaml(DATA_DIR / "requirements.yaml")
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    errors, metrics = validate_inputs(system, assumptions, requirements)

    if errors:
        print("Input validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Input validation passed")
    print(f"- Elements: {metrics['elements']}")
    print(f"- Interfaces: {metrics['interfaces']}")
    print(f"- Assumptions: {metrics['assumptions']}")
    print(f"- Requirements: {metrics['requirements']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
