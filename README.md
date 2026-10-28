# SafeStop AI-FMEA Pipeline

SafeStop-AI explores how AI can support the first draft of an FMEA while keeping engineering review, correction and safety decisions under human control.

📘 **[Read the complete project documentation](docs/PROJECT_DOCUMENTATION.md)**

## Project Highlights

- Structured system, assumption and requirement evidence in YAML
- 29 preliminary AI-generated FMEA candidates in TRIAL-01
- Python checks for input structure, traceability, duplicate mechanisms and prohibited safety claims
- GitHub Actions-based validation and report generation
- Optional manual Gemini API generation with validated JSON and run provenance
- Editable Excel workbook for human review, with illustrative S/O/D and RPN fields
- Explicit uncertainty, traceability and human-in-the-loop controls

## Workflow

1. Prepare controlled system evidence in YAML
2. Generate structured FMEA candidates using a controlled prompt
3. Validate the candidate JSON using Python and GitHub Actions
4. Generate Markdown and Excel review reports
5. Perform human review and illustrative S/O/D-RPN screening
6. Record corrections and retain independent verification evidence outside the AI output

## Free-tier API integration

The optional **Generate FMEA with Gemini** workflow connects the controlled YAML
evidence and existing prompt to Gemini, validates the returned candidates, and
builds Markdown and Excel review reports. It makes **one API request per manual
run**, with no automatic retries. Push and pull-request validation makes no API
calls. Existing TRIAL-01 evidence and the manual report workflow remain available.

1. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey).
   Use a project marked **Free** and leave paid billing disabled to stay within
   the free tier. Eligibility and quotas depend on your project and region.
2. In this repository, open **Settings → Secrets and variables → Actions → New
   repository secret**. Name it `GEMINI_API_KEY` and paste the key as its value.
   Keep the key out of source files, issues and chat messages.
3. Open **Actions → Generate FMEA with Gemini → Run workflow**. Run the default
   **connection-test** mode first. It sends one small JSON request with a 60-second
   socket timeout and does not generate candidates or reports. A pass checks
   credentials/provider access, not the full FMEA schema or engineering quality.
4. After the connection test passes, run again with **mode: generate** and
   TRIAL-02 or TRIAL-03. This sends one full FMEA request with a 300-second socket
   timeout. The workflow has a 10-minute job limit. There are no automatic retries.
5. Download the generation run artifact. Review `fmea_candidates.json`, its metadata file,
   `fmea_report.md` and `fmea_report.xlsx`. The workflow does not commit results.
   Commit a reviewed trial separately when you want to retain it in the repo.

The current model is `gemini-3.5-flash-lite`, listed as free-tier eligible on
2026-10-28. Free-tier access is limited, not unlimited. A quota error stops the
run; it does not switch to a paid provider. The code cannot determine your
project billing tier. If billing is enabled, requests may be charged.
Check [current pricing](https://ai.google.dev/gemini-api/docs/pricing) and
[your quota](https://ai.google.dev/gemini-api/docs/rate-limits) before running.
Google's free-tier data terms may allow submitted content to improve products;
use this repository's fictional evidence and check the terms before sending
confidential engineering information.

For a local setup check without a key or API call:

```bash
python -m pip install -r requirements.txt
python -m src.generate_candidates --dry-run --output outputs/TRIAL-02/fmea_candidates.json
```

For generation, set `GEMINI_API_KEY` securely in your shell environment, then run:

```bash
python -m src.generate_candidates --connection-test
# After the connection test passes:
python -m src.generate_candidates --output outputs/TRIAL-02/fmea_candidates.json
python -m src.validate_candidates outputs/TRIAL-02/fmea_candidates.json
python -m src.render_report outputs/TRIAL-02/fmea_candidates.json --trial-id TRIAL-02 --output outputs/TRIAL-02/fmea_report.md
python -m src.render_xlsx outputs/TRIAL-02/fmea_candidates.json --trial-id TRIAL-02 --output outputs/TRIAL-02/fmea_report.xlsx
```

Use a fresh output directory for each local run; existing outputs are never
overwritten. Metadata records source/request/output hashes, requested model,
time, interaction ID and reported token usage. Failed, empty, truncated,
schema-invalid or semantically rejected output does not produce a candidate
file. Passing these checks is screening only; causal correctness, coverage,
S/O/D and safety decisions still require human review.

If a request times out, the provider may still have processed it. A timeout does
not prove an invalid key. Use the small connection test to distinguish a basic
access problem from a slow or failing full generation. DNS, TLS, HTTP and timeout
failures have separate messages; credentials and raw provider bodies are never
logged. A longer generation timeout is a bounded allowance, not a confirmed fix
for the first live TRIAL-02 timeout.

The initial `gemini-3.8-flash` model timed out both for full TRIAL-02 generation
and for a tiny connection test. The Flash-Lite model is an explicit alternative
for a controlled comparison using the same endpoint, credentials, request format
and deadlines. It is not an automatic fallback or proof that the original model
caused the timeouts. Check the connection test before generating a new trial.
Record the requested model when comparing trials; a faster model does not
establish FMEA correctness or coverage. Official model capabilities, including
structured output, are documented
[here](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite).

The REST response parser uses the interaction's `status: completed`. An individual
`model_output` step may omit `status`, as shown in the official
[API reference](https://ai.google.dev/api/interactions-api). Completed output
still needs non-empty text, valid JSON and all existing candidate checks.

## System Under Study

The fictional safety function contains:

- Dual-channel E-stop inputs
- Safety controller
- Independent outputs Q1/Q2
- Series contactors K1/K2
- EDM feedback
- Manual reset
- 24 V control supply

The architecture assumes that either K1 or K2 opening is sufficient to remove drive power.

## TRIAL-01

TRIAL-01 contains 29 preliminary AI-generated candidate failure modes. They are screening inputs for human review, not an independently validated FMEA or a benchmark result.

The review workbook records illustrative Severity, Occurrence and Detectability inputs and calculates RPN only after those values are entered by a human reviewer.

## Engineering Findings

- Architecture definition strongly affects candidate quality.
- Some AI candidates bundle more than one physical mechanism and require human correction.
- Explicit assumptions and missing-information fields make unsupported conclusions visible.
- Human review remains mandatory for all safety decisions.

## Repository Outputs

- Versioned TRIAL-01 candidate JSON
- Editable human-review Excel workbook
- Markdown and Excel reports generated as GitHub Actions artifacts
- Project documentation and portfolio website

## Skills Demonstrated

- FMEA and causal-chain analysis
- Functional safety reasoning
- Requirements and traceability
- AI governance
- YAML / JSON
- Python validation
- GitHub Actions
- Engineering review and RPN screening

## Portfolio Website

https://aparna3498.github.io/safestop-fmea-pipeline/

## Disclaimer

This project is a fictional documentation and simulation exercise for portfolio purposes only.

It does not verify a real machine, determine SIL/PL, prove standards compliance, provide certification evidence or replace human safety assessment.
