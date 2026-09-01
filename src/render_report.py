"""Render validated FMEA candidates as a human-review Markdown report."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from .fmea_models import FMEACandidate
from .validate_candidates import validate_candidate_file


def clean(value: str) -> str:
    """Keep generated text readable in Markdown tables and list items."""
    return " ".join(value.split()).replace("|", "\\|")


def list_text(values: list[str]) -> str:
    if not values:
        return "None stated"
    return "; ".join(clean(value) for value in values)


def render_summary(candidates: list[FMEACandidate]) -> list[str]:
    classifications = Counter(item.ai_classification.value for item in candidates)
    confidences = Counter(item.confidence.value for item in candidates)

    lines = [
        "## Screening summary",
        "",
        f"Total candidates: **{len(candidates)}**",
        "",
        "| AI classification | Count |",
        "| --- | ---: |",
    ]
    for label in ("Safe", "Degraded", "Dangerous", "Dangerous latent", "Uncertain"):
        lines.append(f"| {label} | {classifications[label]} |")

    lines.extend(
        [
            "",
            "| Confidence | Count |",
            "| --- | ---: |",
        ]
    )
    for label in ("High", "Medium", "Low"):
        lines.append(f"| {label} | {confidences[label]} |")
    return lines


def render_candidate(candidate: FMEACandidate) -> list[str]:
    return [
        f"## {candidate.candidate_id} — {clean(candidate.element_id)}",
        "",
        f"- **Failure mode:** {clean(candidate.failure_mode)}",
        f"- **Local effect:** {clean(candidate.local_effect)}",
        f"- **System effect:** {clean(candidate.system_effect)}",
        f"- **Potential hazardous consequence:** {clean(candidate.hazardous_consequence)}",
        f"- **Detection mechanism:** {clean(candidate.detection_mechanism)}",
        f"- **Recommended action:** {clean(candidate.recommended_action)}",
        f"- **Evidence references:** {list_text(candidate.evidence_references)}",
        f"- **Confidence:** {candidate.confidence.value}",
        f"- **Assumptions:** {list_text(candidate.assumptions)}",
        f"- **Missing information:** {list_text(candidate.missing_information)}",
        f"- **AI screening classification:** {candidate.ai_classification.value}",
        "",
        "**Human review:** ☐ Accept for comparison ☐ Correct ☐ Reject",
        "",
        "**Reviewer notes:**",
        "",
    ]


def render_report(candidates: list[FMEACandidate], trial_id: str) -> str:
    lines = [
        "# Preliminary AI-FMEA Candidate Report",
        "",
        f"Trial: **{trial_id}**",
        "",
        "> This report contains AI-generated candidates for human review. It does not "
        "approve an FMEA, verify safety, demonstrate compliance, assign SIL/PL, or "
        "provide acceptance evidence.",
        "",
        "The causal chains and screening labels depend on the supplied fictional "
        "system definition, draft requirements and unverified assumptions.",
        "",
        *render_summary(candidates),
        "",
    ]
    for candidate in candidates:
        lines.extend(render_candidate(candidate))
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_file", type=Path)
    parser.add_argument("--trial-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates, errors = validate_candidate_file(args.candidate_file)
    if errors:
        print("Report not generated because candidate validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        render_report(candidates, args.trial_id),
        encoding="utf-8",
    )
    print(f"Wrote report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
