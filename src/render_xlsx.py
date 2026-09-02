"""Render preliminary FMEA candidates as an editable Excel review workbook."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import xlsxwriter


REQUIRED_FIELDS = (
    "candidate_id",
    "element_id",
    "failure_mode",
    "local_effect",
    "system_effect",
    "hazardous_consequence",
    "detection_mechanism",
    "recommended_action",
    "evidence_references",
    "confidence",
    "assumptions",
    "missing_information",
    "ai_classification",
)

CLASSIFICATIONS = (
    "Safe",
    "Degraded",
    "Dangerous",
    "Dangerous latent",
    "Uncertain",
)

CONFIDENCES = ("High", "Medium", "Low")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_file", type=Path)
    parser.add_argument("--trial-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def load_candidates(path: Path) -> list[dict[str, Any]]:
    """Load candidates after the dedicated validation step has passed."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read candidate JSON: {exc}") from exc

    if not isinstance(payload, list) or not payload:
        raise ValueError("Candidate JSON must be a non-empty array.")

    for index, candidate in enumerate(payload, start=1):
        if not isinstance(candidate, dict):
            raise ValueError(f"Candidate {index} must be a JSON object.")
        missing = [field for field in REQUIRED_FIELDS if field not in candidate]
        if missing:
            raise ValueError(
                f"Candidate {index} is missing required fields: {', '.join(missing)}"
            )
    return payload


def list_text(value: Any) -> str:
    if not value:
        return "None stated"
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return str(value)


def safe_table_name(trial_id: str) -> str:
    suffix = re.sub(r"[^A-Za-z0-9_]", "_", trial_id)
    return f"FMEA_{suffix}"[:255]


def render_workbook(
    candidates: list[dict[str, Any]], trial_id: str, output: Path
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    workbook = xlsxwriter.Workbook(output)
    workbook.set_properties(
        {
            "title": "Preliminary AI-FMEA Candidate Report",
            "subject": f"Human-review workbook for {trial_id}",
            "comments": (
                "AI-generated screening candidates only; not approval, verification, "
                "acceptance evidence, or a compliance determination."
            ),
        }
    )

    navy = "#17365D"
    teal = "#0F6B78"
    light_blue = "#D9EAF7"
    pale_yellow = "#FFF2CC"
    light_gray = "#E7E6E6"
    dark_gray = "#404040"
    white = "#FFFFFF"

    title_format = workbook.add_format(
        {
            "bold": True,
            "font_size": 18,
            "font_color": white,
            "bg_color": navy,
            "align": "left",
            "valign": "vcenter",
        }
    )
    subtitle_format = workbook.add_format(
        {"bold": True, "font_size": 11, "font_color": navy}
    )
    note_format = workbook.add_format(
        {
            "font_size": 10,
            "font_color": dark_gray,
            "bg_color": pale_yellow,
            "text_wrap": True,
            "valign": "vcenter",
            "border": 1,
            "border_color": "#D6B656",
        }
    )
    section_format = workbook.add_format(
        {
            "bold": True,
            "font_color": white,
            "bg_color": teal,
            "align": "left",
            "valign": "vcenter",
        }
    )
    label_format = workbook.add_format(
        {"bold": True, "bg_color": light_blue, "border": 1, "border_color": white}
    )
    count_format = workbook.add_format(
        {"align": "center", "border": 1, "border_color": white, "num_format": "0"}
    )
    text_format = workbook.add_format(
        {"text_wrap": True, "valign": "top", "font_size": 9}
    )
    id_format = workbook.add_format(
        {"valign": "top", "align": "center", "font_size": 9}
    )
    review_format = workbook.add_format(
        {"text_wrap": True, "valign": "top", "font_size": 9, "bg_color": pale_yellow}
    )

    summary = workbook.add_worksheet("Summary")
    summary.hide_gridlines(2)
    summary.set_tab_color(navy)
    summary.set_column("A:A", 24)
    summary.set_column("B:B", 14)
    summary.set_column("C:C", 4)
    summary.set_column("D:D", 22)
    summary.set_column("E:E", 14)
    summary.set_column("F:F", 4)
    summary.set_row(0, 30)
    summary.merge_range("A1:F1", "Preliminary AI-FMEA Candidate Report", title_format)
    summary.write("A2", "Trial", subtitle_format)
    summary.write("B2", trial_id)
    summary.write("D2", "Total candidates", subtitle_format)
    summary.write_formula(
        "E2",
        "=COUNTA('FMEA Candidates'!$A$2:$A$1048576)",
        count_format,
        len(candidates),
    )
    summary.set_row(3, 54)
    summary.merge_range(
        "A4:F4",
        (
            "Human review required. This workbook contains AI-generated candidates "
            "for a fictional system. It does not approve an FMEA, verify safety, "
            "demonstrate compliance, assign SIL/PL, or provide acceptance evidence."
        ),
        note_format,
    )

    summary.merge_range("A6:B6", "AI classification", section_format)
    summary.merge_range("D6:E6", "Confidence", section_format)
    summary.write_row("A7", ["Classification", "Count"], label_format)
    summary.write_row("D7", ["Confidence", "Count"], label_format)

    classification_counts = Counter(
        str(candidate["ai_classification"]) for candidate in candidates
    )
    confidence_counts = Counter(str(candidate["confidence"]) for candidate in candidates)
    last_data_row = len(candidates) + 1

    for offset, label in enumerate(CLASSIFICATIONS, start=7):
        excel_row = offset + 1
        summary.write(offset, 0, label)
        summary.write_formula(
            offset,
            1,
            f'=COUNTIF(\'FMEA Candidates\'!$M$2:$M${last_data_row},A{excel_row})',
            count_format,
            classification_counts[label],
        )

    for offset, label in enumerate(CONFIDENCES, start=7):
        excel_row = offset + 1
        summary.write(offset, 3, label)
        summary.write_formula(
            offset,
            4,
            f'=COUNTIF(\'FMEA Candidates\'!$J$2:$J${last_data_row},D{excel_row})',
            count_format,
            confidence_counts[label],
        )

    summary.merge_range("A15:B15", "Human review status", section_format)
    summary.write_row("A16", ["Disposition", "Count"], label_format)
    review_labels = ("Not reviewed", "Accept for comparison", "Correct", "Reject")
    for offset, label in enumerate(review_labels, start=16):
        excel_row = offset + 1
        summary.write(offset, 0, label)
        cached = len(candidates) if label == "Not reviewed" else 0
        summary.write_formula(
            offset,
            1,
            f'=COUNTIF(\'FMEA Candidates\'!$N$2:$N${last_data_row},A{excel_row})',
            count_format,
            cached,
        )

    summary.write("D15", "Workflow", section_format)
    summary.merge_range(
        "D16:E19",
        (
            "1. Review each causal chain.\n"
            "2. Record disposition and score category.\n"
            "3. Add corrections and notes.\n"
            "4. Do not use AI output as acceptance evidence."
        ),
        text_format,
    )
    summary.freeze_panes(5, 0)
    summary.set_landscape()
    summary.fit_to_pages(1, 1)
    summary.set_footer("&LPreliminary AI-FMEA&C" + trial_id + "&RPage &P of &N")

    sheet = workbook.add_worksheet("FMEA Candidates")
    sheet.hide_gridlines(2)
    sheet.set_tab_color(teal)
    sheet.freeze_panes(1, 2)
    sheet.set_landscape()
    sheet.fit_to_pages(1, 0)
    sheet.repeat_rows(0)
    sheet.set_footer("&LHuman review required&C" + trial_id + "&RPage &P of &N")

    headers = [
        "Candidate ID",
        "Element ID",
        "Failure mode",
        "Local effect",
        "System effect",
        "Potential hazardous consequence",
        "Detection mechanism",
        "Recommended action",
        "Evidence references",
        "Confidence",
        "Assumptions",
        "Missing information",
        "AI classification",
        "Human disposition",
        "Score category",
        "Reviewer corrections",
        "Reviewer notes",
    ]

    rows: list[list[str]] = []
    for candidate in candidates:
        rows.append(
            [
                str(candidate["candidate_id"]),
                str(candidate["element_id"]),
                str(candidate["failure_mode"]),
                str(candidate["local_effect"]),
                str(candidate["system_effect"]),
                str(candidate["hazardous_consequence"]),
                str(candidate["detection_mechanism"]),
                str(candidate["recommended_action"]),
                list_text(candidate["evidence_references"]),
                str(candidate["confidence"]),
                list_text(candidate["assumptions"]),
                list_text(candidate["missing_information"]),
                str(candidate["ai_classification"]),
                "Not reviewed",
                "",
                "",
                "",
            ]
        )

    for row_index, row in enumerate(rows, start=1):
        for column_index, value in enumerate(row):
            cell_format = review_format if column_index >= 13 else text_format
            if column_index in (0, 1, 9, 12, 13):
                cell_format = id_format if column_index < 13 else review_format
            sheet.write(row_index, column_index, value, cell_format)
        sheet.set_row(row_index, 96)

    table_columns = []
    for column_index, header in enumerate(headers):
        column_format = review_format if column_index >= 13 else text_format
        if column_index in (0, 1, 9, 12):
            column_format = id_format
        table_columns.append({"header": header, "format": column_format})

    sheet.add_table(
        0,
        0,
        len(rows),
        len(headers) - 1,
        {
            "name": safe_table_name(trial_id),
            "style": "Table Style Medium 2",
            "columns": table_columns,
        },
    )
    sheet.set_row(0, 38)

    widths = [12, 13, 38, 36, 42, 42, 38, 40, 34, 12, 34, 38, 18, 22, 18, 38, 38]
    for column_index, width in enumerate(widths):
        sheet.set_column(column_index, column_index, width)

    disposition_range = f"N2:N{last_data_row}"
    sheet.data_validation(
        disposition_range,
        {
            "validate": "list",
            "source": list(review_labels),
            "input_title": "Human disposition",
            "input_message": "Select a human-review outcome.",
            "error_title": "Use the review list",
            "error_message": "Choose one of the supplied disposition values.",
        },
    )

    classification_colors = {
        "Safe": ("#E2F0D9", "#375623"),
        "Degraded": ("#FFF2CC", "#7F6000"),
        "Dangerous": ("#F4CCCC", "#9C0006"),
        "Dangerous latent": ("#FCE4D6", "#9C5700"),
        "Uncertain": (light_gray, dark_gray),
    }
    for label, (fill, font) in classification_colors.items():
        sheet.conditional_format(
            f"M2:M{last_data_row}",
            {
                "type": "text",
                "criteria": "containing",
                "value": label,
                "format": workbook.add_format({"bg_color": fill, "font_color": font}),
            },
        )

    review_colors = {
        "Not reviewed": (pale_yellow, dark_gray),
        "Accept for comparison": ("#E2F0D9", "#375623"),
        "Correct": ("#D9EAF7", navy),
        "Reject": ("#F4CCCC", "#9C0006"),
    }
    for label, (fill, font) in review_colors.items():
        sheet.conditional_format(
            disposition_range,
            {
                "type": "text",
                "criteria": "containing",
                "value": label,
                "format": workbook.add_format({"bg_color": fill, "font_color": font}),
            },
        )

    sheet.write_comment(
        "N1",
        "Human assessor field. AI output must not determine this disposition.",
    )
    sheet.write_comment(
        "O1",
        "Enter the score category defined by the human review process.",
    )

    workbook.close()


def main() -> int:
    args = parse_args()
    try:
        candidates = load_candidates(args.candidate_file)
        render_workbook(candidates, args.trial_id, args.output)
    except (ValueError, OSError, xlsxwriter.exceptions.XlsxWriterException) as exc:
        print(f"Excel report not generated: {exc}")
        return 1

    print(f"Wrote Excel report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
