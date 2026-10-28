"""Generate preliminary FMEA candidates with one Gemini API request."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from .fmea_models import FMEACandidate, FMEAResponse
from .validate_candidates import evidence_id_sets, semantic_errors
from .validate_inputs import DATA_DIR, PROJECT_ROOT, load_yaml, validate_inputs


ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
# Listed as free-tier eligible on 2026-10-28; the project must also be on Free.
MODEL = "gemini-3.8-flash"
SOURCE_PATHS = (
    "prompts/fmea_prompt.md",
    "data/system.yaml",
    "data/assumptions.yaml",
    "data/requirements.yaml",
)


def build_request() -> tuple[dict[str, object], dict[str, str]]:
    """Validate controlled inputs and include only the prompt and YAML evidence."""
    evidence = [load_yaml(DATA_DIR / name) for name in (
        "system.yaml", "assumptions.yaml", "requirements.yaml"
    )]
    errors, _ = validate_inputs(*evidence)
    if errors:
        raise ValueError("Source evidence validation failed:\n" + "\n".join(errors))

    sources = {path: (PROJECT_ROOT / path).read_text(encoding="utf-8")
               for path in SOURCE_PATHS}
    prompt = sources["prompts/fmea_prompt.md"]
    for path in SOURCE_PATHS[1:]:
        prompt += f"\n\n# Supplied evidence: {path}\n```yaml\n{sources[path]}\n```"
    boundary_ids, evidence_ids = evidence_id_sets()
    prompt += (
        "\n\n# Output contract\nReturn an object with a non-empty `candidates` array "
        "matching the supplied JSON schema. Generate distinct candidates across the "
        "analysis boundary; do not aim for a preset count. Do not assign S/O/D or RPN.\n"
        f"Allowed element/interface IDs: {', '.join(sorted(boundary_ids))}\n"
        f"Allowed evidence IDs: {', '.join(sorted(evidence_ids))}\n"
        "Every candidate must cite at least one A- or SR- ID."
    )
    payload = {
        "model": MODEL,
        "input": prompt,
        "store": False,
        "generation_config": {"max_output_tokens": 16384},
        "response_format": {
            "type": "text",
            "mime_type": "application/json",
            "schema": FMEAResponse.model_json_schema(),
        },
    }
    hashes = {path: hashlib.sha256(content.encode("utf-8")).hexdigest()
              for path, content in sources.items()}
    return payload, hashes


def call_gemini(payload: dict[str, object], api_key: str) -> dict[str, object]:
    """Make one request without retries or logging credentials/provider bodies."""
    request = Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urlopen(request, timeout=180) as response:
            result = json.load(response)
    except HTTPError as exc:
        hints = {
            400: "Check the API schema/model and project free-tier eligibility.",
            401: "Check GEMINI_API_KEY.",
            403: "Check API key permissions and project/region eligibility.",
            404: "Check current model availability in Google AI Studio.",
            429: "Free-tier quota/rate limit reached; wait and rerun manually.",
        }
        raise ValueError(
            f"Gemini HTTP {exc.code}. "
            + hints.get(exc.code, "Provider error; try again later manually.")
            + " No automatic retry was made."
        ) from None
    except (URLError, TimeoutError, OSError):
        raise ValueError("Gemini connection failed or timed out. No automatic retry was made.") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("Gemini returned an invalid JSON response.") from None
    except ValueError:
        # An invalid header (for example a pasted newline) can echo its value.
        raise ValueError("Invalid Gemini request. Check the API key for pasted newlines.") from None
    if not isinstance(result, dict):
        raise ValueError("Gemini returned an unexpected response shape.")
    return result


def parse_candidates(response: dict[str, object]) -> list[FMEACandidate]:
    """Reject incomplete/blocked output, then enforce the existing review contract."""
    if response.get("status") != "completed":
        raise ValueError("Gemini did not complete generation; no candidate file was written.")
    steps = response.get("steps")
    if not isinstance(steps, list):
        raise ValueError("Gemini response has no output steps.")
    texts: list[str] = []
    for step in steps:
        if not isinstance(step, dict) or step.get("type") != "model_output":
            continue
        if step.get("status") != "done" or not isinstance(step.get("content"), list):
            raise ValueError("Gemini returned an incomplete model output step.")
        for part in step["content"]:
            if not isinstance(part, dict) or part.get("type") != "text":
                raise ValueError("Gemini returned non-text or blocked output.")
            if not isinstance(part.get("text"), str):
                raise ValueError("Gemini returned an invalid text part.")
            texts.append(part["text"])
    if not texts:
        raise ValueError("Gemini returned no candidate text.")
    try:
        candidates = FMEAResponse.model_validate_json("".join(texts)).candidates
    except ValidationError:
        raise ValueError("Generated JSON failed the FMEA output schema; no candidate file was written.") from None
    errors = semantic_errors(candidates, *evidence_id_sets())
    if errors:
        raise ValueError("Generated candidates failed validation:\n" + "\n".join(errors))
    return candidates


def generate(output: Path, dry_run: bool = False) -> int:
    """Write validated candidates as the array expected by the report renderers."""
    metadata_path = output.with_name(output.stem + ".metadata.json")
    if output.exists() or metadata_path.exists():
        raise ValueError("Output already exists. Choose a new output directory for each run.")
    payload, source_hashes = build_request()
    if dry_run:
        print(f"Dry run passed: evidence and request schema ready for {MODEL}. No API call made.")
        return 0
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY in your environment or GitHub Actions repository secrets.")
    response = call_gemini(payload, api_key)
    candidates = parse_candidates(response)
    candidate_json = json.dumps(
        [item.model_dump(mode="json") for item in candidates], indent=2, ensure_ascii=False
    ) + "\n"
    metadata = {
        "provider": "Google Gemini Developer API",
        "model_requested": MODEL,
        "endpoint": ENDPOINT,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "interaction_id": response.get("id"),
        "usage": response.get("usage"),
        "source_sha256": source_hashes,
        "request_sha256": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
        "candidate_sha256": hashlib.sha256(candidate_json.encode("utf-8")).hexdigest(),
        "candidate_count": len(candidates),
        "validation": "Schema and semantic screening passed; human review required",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        stream.write(candidate_json)
    with metadata_path.open("x", encoding="utf-8") as stream:
        json.dump(metadata, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(f"Wrote {len(candidates)} preliminary candidates: {output}. Human review required.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true", help="Validate request setup without an API key or call")
    args = parser.parse_args()
    try:
        return generate(args.output, args.dry_run)
    except (ValueError, OSError) as exc:
        print(f"Generation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
