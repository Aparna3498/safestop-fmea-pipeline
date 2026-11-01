# SafeStop AI-FMEA Pipeline

SafeStop generates preliminary Failure Mode and Effects Analysis (FMEA) candidates for a fictional industrial robot emergency-stop system. It combines structured system information, the Gemini API and Python checks to produce reports for engineering review.

[Project website](https://aparna3498.github.io/safestop-fmea-pipeline/) · [Project background](docs/PROJECT_DOCUMENTATION.md)

## How it works

1. **Read the inputs:** system architecture, assumptions and draft safety requirements stored in YAML.
2. **Generate candidates:** send the inputs and FMEA instructions to Gemini.
3. **Check the response:** validate the JSON structure, evidence references and defined consistency rules.
4. **Create reports:** export the accepted candidates as Markdown and an editable Excel workbook.

Each candidate describes a possible failure and its effects, with supporting references and information for review.

## Example system

The example includes dual-channel emergency-stop inputs, a safety controller, two series contactors, feedback monitoring and manual reset. It assumes either contactor opening is sufficient to remove drive power.

## Run on GitHub

A Gemini API key is required to generate new candidates.

1. In a fork or repository you control, add the key as an Actions secret named `GEMINI_API_KEY`.
2. Open **Actions → Generate FMEA with Gemini → Run workflow**.
3. Run `connection-test` to check API access. Then start a new run in `generate` mode and select a trial label.
4. Download the results from **Artifacts** on the completed run.

To build reports from an existing saved trial without calling Gemini, use **Build FMEA report**.

## Outputs

| File | Contents |
| --- | --- |
| `fmea_candidates.json` | Structured FMEA candidates |
| `fmea_candidates.metadata.json` | Model, timing and input/output fingerprints |
| `fmea_report.md` | Readable text report |
| `fmea_report.xlsx` | Editable engineering-review workbook |

Workflow artifacts are retained for 30 days and are not committed automatically.

## Main files

- `data/` — system description, assumptions and requirements
- `prompts/` — FMEA generation instructions
- `src/` — API integration, validation and report generation
- `trials/` — saved candidate datasets
- `.github/workflows/` — GitHub Actions workflows

## Engineering review

AI-generated candidates require human review of their reasoning, coverage and safety implications. Severity, Occurrence and Detectability ratings are entered by an engineer; the workbook calculates RPN after those entries.

This fictional demonstration does not verify a real machine or establish standards compliance, SIL/PL or certification.
