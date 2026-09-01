# SafeStop AI-FMEA Pipeline

A human-in-the-loop AI pipeline for preliminary FMEA of a fictional industrial
robot emergency-stop system.

## What the project does

The pipeline:

1. reads a structured system definition, assumptions and safety requirements;
2. validates IDs, required fields and traceability;
3. generates candidate failure modes with an OpenAI model;
4. validates the candidate structure, evidence references and screening labels;
5. renders a Markdown report for human assessment.

The AI output is candidate material only. It does not approve an FMEA,
demonstrate functional-safety compliance, assign SIL or PL, replace verification
evidence or make a final safety decision.

## Repository structure

```text
data/                         source evidence
prompts/fmea_prompt.md        evidence-only FMEA instructions
schemas/                      generated JSON output contract
src/                          validation, generation and reporting code
tests/                        automated pipeline checks
.github/workflows/            GitHub Actions pipelines
```

## Automatic validation

Every push and pull request runs **Validate safety inputs**. The workflow checks
the YAML evidence, JSON schema, Python code, unit tests and prompt construction.
It does not call the model and therefore does not incur model usage cost.

## Generate a trial report

Generation is deliberately manual:

1. Create an OpenAI API key.
2. In the GitHub repository, open **Settings → Secrets and variables → Actions**.
3. Create a repository secret named `OPENAI_API_KEY`.
4. Open **Actions → Generate FMEA report → Run workflow**.
5. Select `TRIAL-01`, `TRIAL-02` or `TRIAL-03`, then run the workflow.
6. Download the generated artifact from the completed workflow run.

The artifact contains:

- `fmea_candidates.json` — structured AI candidates;
- `fmea_report.md` — report with human-review fields;
- `run_metadata.json` — trial and model traceability.

The workflow uses the OpenAI Responses API with Structured Outputs. The API key
is read from the GitHub secret and is never stored in the repository.

## Local checks

```bash
python -m pip install -r requirements.txt
python src/validate_inputs.py
python -m src.export_schema --check
python -m unittest discover -s tests -v
python -m src.generate_fmea --trial-id TRIAL-01 --dry-run
```

The dry run builds the exact prompt package without calling the API.

## Project status

- Day 1: repository, structured evidence and automatic input validation — complete.
- Day 2: structured AI generation, candidate validation and report rendering — complete.
- Next: run controlled trials and compare candidates with the human reference FMEA.
