# SafeStop AI-FMEA Pipeline

A human-in-the-loop AI pipeline for preliminary FMEA of a fictional industrial
robot emergency-stop system.

## What the project does

The free portfolio workflow:

1. reads a structured system definition, assumptions and safety requirements;
2. validates IDs, required fields and traceability;
3. uses ChatGPT interactively to generate preliminary FMEA candidates;
4. stores each trial as a traceable JSON file;
5. validates candidate structure, evidence references and screening labels;
6. renders a Markdown report for human assessment.

The AI output is candidate material only. It does not approve an FMEA,
demonstrate functional-safety compliance, assign SIL or PL, replace verification
evidence or make a final safety decision.

## Repository structure

```text
data/                         source evidence
prompts/fmea_prompt.md        evidence-only FMEA instructions
schemas/                      generated JSON output contract
trials/TRIAL-01/              committed ChatGPT candidate set
src/                          validation and reporting code
tests/                        automated pipeline checks
.github/workflows/            GitHub Actions pipelines
```

## Why generation is manual

The candidate-generation step runs in ChatGPT rather than through the paid
OpenAI API. This keeps the portfolio exercise free of additional API charges
while preserving a deliberate human-in-the-loop transfer and review step.

The generation prompt uses only `data/system.yaml`, `data/assumptions.yaml` and
`data/requirements.yaml`. The reference FMEA is deliberately excluded from the
generation evidence.

## Automatic validation

Every push and pull request runs **Validate safety inputs**. It checks:

- the three YAML evidence files;
- the JSON Schema and Python sources;
- unit tests;
- all 29 `TRIAL-01` candidates;
- evidence IDs, boundary IDs, sequential IDs and duplicate mechanisms;
- prohibited SIL, PL, certification and compliance claims;
- report rendering.

## Build the TRIAL-01 report

1. Open **Actions → Build FMEA report**.
2. Click **Run workflow**.
3. Select `TRIAL-01` and run it.
4. Download the `safestop-TRIAL-01` artifact.

The artifact contains:

- `fmea_candidates.json` — structured AI candidates;
- `fmea_report.md` — report with human-review fields.

No API key is required by either workflow.

## Local checks

```bash
python -m pip install -r requirements.txt
python src/validate_inputs.py
python -m src.export_schema --check
python -m unittest discover -s tests -v
python -m src.validate_candidates trials/TRIAL-01/fmea_candidates.json
python -m src.render_report trials/TRIAL-01/fmea_candidates.json \
  --trial-id TRIAL-01 --output outputs/TRIAL-01/fmea_report.md
```

## Project status

- Day 1: repository, structured evidence and automatic input validation — complete.
- Day 2: ChatGPT candidate generation, validation and report rendering — complete.
- Next: human review and comparison against the excluded reference FMEA.
