"""Offline API contract, failure handling and generation regression tests."""

from __future__ import annotations

import hashlib
import io
import json
import os
import socket
import ssl
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from src import generate_candidates as api


FIXTURE = api.PROJECT_ROOT / "trials/TRIAL-01/fmea_candidates.json"


def response_for(candidates: object = None) -> dict[str, object]:
    if candidates is None:
        candidates = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return {
        "id": "offline-fixture",
        "status": "completed",
        "steps": [
            {"type": "thought", "content": []},
            {"type": "model_output", "content": [
                {"type": "text", "text": json.dumps({"candidates": candidates})}
            ]},
        ],
        "usage": {"total_tokens": 100},
    }


class GenerationTests(unittest.TestCase):
    def test_official_response_shape_without_step_status_passes(self) -> None:
        response = response_for()
        self.assertNotIn("status", response["steps"][1])
        self.assertEqual(len(api.parse_candidates(response)), 29)

    def test_migration_example_with_explicit_done_status_still_passes(self) -> None:
        response = response_for()
        response["steps"][1]["status"] = "done"
        self.assertEqual(len(api.parse_candidates(response)), 29)

    def test_request_uses_controlled_evidence_and_schema(self) -> None:
        payload, hashes = api.build_request()
        self.assertFalse(payload["store"])
        self.assertEqual(payload["model"], api.MODEL)
        self.assertEqual(set(hashes), set(api.SOURCE_PATHS))
        self.assertIn("A-006", payload["input"])
        self.assertNotIn("TRIAL-01", payload["input"])
        self.assertIn("candidates", payload["response_format"]["schema"]["properties"])

    @patch.object(api, "urlopen")
    @patch.object(api, "validate_inputs", return_value=(["broken evidence"], {}))
    def test_invalid_evidence_stops_before_network(self, validate, network) -> None:
        with self.assertRaisesRegex(ValueError, "Source evidence validation failed"):
            api.build_request()
        network.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(api, "urlopen")
    def test_dry_run_needs_no_key_and_writes_nothing(self, network) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "new/fmea_candidates.json"
            self.assertEqual(api.generate(output, dry_run=True), 0)
            self.assertFalse(output.parent.exists())
        network.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(api, "urlopen")
    def test_missing_key_stops_before_network(self, network) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Set GEMINI_API_KEY"):
                api.generate(Path(directory) / "candidates.json")
        network.assert_not_called()

    @patch.object(api, "call_gemini")
    def test_existing_candidate_or_metadata_is_preserved(self, call) -> None:
        for name in ("candidates.json", "candidates.metadata.json"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                existing = Path(directory) / name
                existing.write_text("previous run", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "already exists"):
                    api.generate(Path(directory) / "candidates.json")
                self.assertEqual(existing.read_text(), "previous run")
        call.assert_not_called()

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret-never-log"})
    @patch.object(api, "urlopen")
    def test_http_to_validated_array_and_provenance(self, network) -> None:
        network.return_value = io.BytesIO(json.dumps(response_for()).encode())
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "candidates.json"
            self.assertEqual(api.generate(output), 0)
            self.assertEqual(len(json.loads(output.read_text())), 29)
            metadata = json.loads(output.with_suffix(".metadata.json").read_text())
            self.assertEqual(metadata["candidate_sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
            self.assertEqual(metadata["interaction_id"], "offline-fixture")
            self.assertNotIn("test-secret", json.dumps(metadata))
        network.assert_called_once()
        request = network.call_args.args[0]
        self.assertEqual(request.full_url, api.ENDPOINT)
        self.assertEqual(request.get_header("X-goog-api-key"), "test-secret-never-log")
        self.assertNotIn(b"test-secret", request.data)

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    @patch.object(api, "call_gemini")
    def test_failed_validation_writes_no_artifacts(self, call) -> None:
        call.return_value = response_for([])
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "schema"):
                api.generate(Path(directory) / "candidates.json")
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_rejects_incomplete_blocked_empty_and_malformed_output(self) -> None:
        invalid = [
            {"status": "incomplete"},
            {"status": "failed"},
            {"status": "completed", "steps": []},
            {"status": "completed", "steps": [{"type": "model_output"}]},
            {"status": "completed", "steps": [{"type": "model_output", "status": "done", "content": [{"type": "refusal"}]}]},
            {"status": "completed", "steps": [{"type": "model_output", "status": "in_progress", "content": []}]},
            {"status": "completed", "steps": [{"type": "model_output", "status": "done", "content": [{"type": "text", "text": "{bad json"}]}]},
            response_for([]),
        ]
        for response in invalid:
            with self.subTest(response=response), self.assertRaises(ValueError):
                api.parse_candidates(response)

    def test_semantic_checks_reject_api_output(self) -> None:
        candidate = json.loads(FIXTURE.read_text())[0]
        changes = (
            {"candidate_id": "AI-009"},
            {"element_id": "invented"},
            {"evidence_references": ["A-999"]},
            {"system_effect": "The system achieves SIL 3"},
            {"risk_score": 10},
        )
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                api.parse_candidates(response_for([{**candidate, **change}]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            api.parse_candidates(response_for([candidate, {**candidate, "candidate_id": "AI-002"}]))

    @patch.object(api, "urlopen")
    def test_http_errors_stop_without_retry_or_secret_exposure(self, network) -> None:
        for code, hint in ((429, "quota"), (403, "permissions"), (500, "Provider error")):
            network.reset_mock()
            network.side_effect = HTTPError(api.ENDPOINT, code, "test-secret", {}, None)
            with self.subTest(code=code), self.assertRaisesRegex(ValueError, hint) as result:
                api.call_gemini({}, "test-secret")
            self.assertNotIn("test-secret", str(result.exception))
            network.assert_called_once()

    @patch.object(api, "urlopen")
    def test_transport_and_envelope_failures_are_reported(self, network) -> None:
        for error in (URLError("test-secret"), TimeoutError("test-secret")):
            network.side_effect = error
            with self.subTest(error=type(error)), self.assertRaisesRegex(ValueError, "connection") as result:
                api.call_gemini({}, "test-secret")
            self.assertNotIn("test-secret", str(result.exception))
        network.side_effect = None
        for body in (b"not json", b"[]"):
            network.return_value = io.BytesIO(body)
            with self.subTest(body=body), self.assertRaises(ValueError):
                api.call_gemini({}, "test-secret")

    @patch.object(api, "urlopen")
    def test_transport_failures_have_distinct_safe_messages(self, network) -> None:
        cases = (
            (TimeoutError("test-secret"), "timed out after 60 seconds"),
            (URLError(TimeoutError("test-secret")), "timed out after 60 seconds"),
            (URLError(socket.gaierror("test-secret")), "DNS lookup failed"),
            (URLError(ssl.SSLError("test-secret")), "TLS connection failed"),
        )
        for error, message in cases:
            network.reset_mock()
            network.side_effect = error
            with self.subTest(error=type(error)), self.assertRaisesRegex(ValueError, message) as result:
                api.call_gemini({}, "test-secret", timeout=60)
            self.assertNotIn("test-secret", str(result.exception))
            network.assert_called_once()

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    @patch.object(api, "urlopen")
    def test_connection_test_makes_one_small_request_without_evidence_or_files(self, network) -> None:
        response = response_for()
        response["steps"][1]["content"][0]["text"] = '{"status":"ok"}'
        network.return_value = io.BytesIO(json.dumps(response).encode())
        with patch.object(api, "build_request") as evidence, patch.object(Path, "open") as files:
            self.assertEqual(api.connection_test(), 0)
            evidence.assert_not_called()
            files.assert_not_called()
        network.assert_called_once()
        self.assertEqual(network.call_args.kwargs["timeout"], 60)
        request = json.loads(network.call_args.args[0].data)
        self.assertNotIn("A-006", request["input"])
        self.assertLess(len(request["input"]), 100)
        self.assertEqual(request["model"], api.MODEL)
        self.assertFalse(request["store"])

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-secret"})
    @patch.object(api, "call_gemini")
    def test_connection_test_rejects_incomplete_or_unexpected_reply(self, call) -> None:
        for text in ('{"status":"wrong"}', 'not json'):
            response = response_for()
            response["steps"][1]["content"][0]["text"] = text
            call.return_value = response
            with self.subTest(text=text), self.assertRaises(ValueError):
                api.connection_test()
        call.return_value = {"status": "incomplete"}
        with self.assertRaises(ValueError):
            api.connection_test()

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(api, "urlopen")
    def test_connection_test_missing_key_stops_before_network(self, network) -> None:
        with self.assertRaisesRegex(ValueError, "Set GEMINI_API_KEY"):
            api.connection_test()
        network.assert_not_called()

    @patch.object(api, "urlopen", side_effect=ValueError("Invalid header: test-secret"))
    def test_malformed_key_is_not_echoed(self, network) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid Gemini request") as result:
            api.call_gemini({}, "test-secret\n")
        self.assertNotIn("test-secret", str(result.exception))


if __name__ == "__main__":
    unittest.main()
