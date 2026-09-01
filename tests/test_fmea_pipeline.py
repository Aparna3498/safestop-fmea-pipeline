"""Unit tests for the Day 2 FMEA output contract and semantic checks."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from src.fmea_models import FMEACandidate
from src.validate_candidates import semantic_errors


def valid_candidate(**overrides: object) -> FMEACandidate:
    payload: dict[str, object] = {
        "candidate_id": "AI-001",
        "element_id": "K1",
        "failure_mode": "Main contact remains closed after coil de-energization",
        "local_effect": "K1 does not interrupt its series power path",
        "system_effect": "K2 can still remove drive power, while redundancy is degraded",
        "hazardous_consequence": "No immediate hazardous consequence under A-006; a later independent failure could prevent power removal",
        "detection_mechanism": "EDM-01 is expected to block reset when K1 feedback does not prove open",
        "recommended_action": "Verify the series path and inject a K1 welded-contact fault",
        "evidence_references": ["A-006", "A-007", "SR-005", "SR-006"],
        "confidence": "Medium",
        "assumptions": [],
        "missing_information": ["Power schematic and contactor data sheet"],
        "ai_classification": "Degraded",
    }
    payload.update(overrides)
    return FMEACandidate.model_validate(payload)


class FMEAModelTests(unittest.TestCase):
    def test_rejects_unknown_classification(self) -> None:
        with self.assertRaises(ValidationError):
            valid_candidate(ai_classification="Critical")

    def test_rejects_extra_field(self) -> None:
        with self.assertRaises(ValidationError):
            valid_candidate(risk_score=10)


class SemanticValidationTests(unittest.TestCase):
    boundary_ids = {"K1", "K2", "CTRL-01"}
    evidence_ids = {"A-006", "A-007", "SR-005", "SR-006", "K1", "K2"}

    def test_valid_candidate_passes(self) -> None:
        errors = semantic_errors(
            [valid_candidate()], self.boundary_ids, self.evidence_ids
        )
        self.assertEqual(errors, [])

    def test_unknown_reference_fails(self) -> None:
        candidate = valid_candidate(evidence_references=["A-999"])
        errors = semantic_errors(
            [candidate], self.boundary_ids, self.evidence_ids
        )
        self.assertTrue(any("unknown evidence reference" in error for error in errors))

    def test_duplicate_mechanism_fails(self) -> None:
        first = valid_candidate()
        second = valid_candidate(candidate_id="AI-002")
        errors = semantic_errors(
            [first, second], self.boundary_ids, self.evidence_ids
        )
        self.assertTrue(any("duplicate" in error for error in errors))

    def test_prohibited_sil_claim_fails(self) -> None:
        candidate = valid_candidate(system_effect="The system achieves SIL 3")
        errors = semantic_errors(
            [candidate], self.boundary_ids, self.evidence_ids
        )
        self.assertTrue(any("prohibited" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
