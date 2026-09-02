# SafeStop AI-FMEA Pipeline

SafeStop-AI explores how AI can support the first draft of an FMEA while keeping engineering review, correction and safety decisions under human control.

📘 **[Read the complete project documentation](docs/PROJECT_DOCUMENTATION.md)**




## Project Highlights

- 29 AI-generated preliminary FMEA candidates
- 83.3% coverage against an 18-row human reference FMEA
- 12 valid additional candidates
- 93.1% usefulness precision
- GitHub Actions-based validation and artifact generation
- Human-in-the-loop review with uncertainty and traceability

## Workflow

1. Prepare controlled system evidence in YAML
2. Generate structured FMEA candidates using a controlled prompt
3. Validate JSON structure using GitHub Actions
4. Generate JSON, Markdown and Excel artifacts
5. Perform human review and illustrative S/O/D-RPN screening
6. Compare results with a predefined reference FMEA

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

## TRIAL-01 Results

| Metric | Result |
|---|---:|
| AI candidates | 29 |
| Reference mechanisms surfaced | 15 / 18 |
| Baseline coverage | 83.3% |
| Valid additions | 12 |
| Duplicate candidates | 1 |
| Usefulness precision | 93.1% |

## Engineering Findings

- Architecture definition strongly affects candidate quality.
- Common-cause failures received higher screening priority.
- Some AI candidates bundled multiple physical mechanisms.
- Low-confidence rows helped expose missing evidence.
- Human review remained mandatory for all safety decisions.

## Repository Outputs

- `fmea_candidates.json`
- `fmea_report.md`
- `fmea_report.xlsx`
- Reference comparison workbook
- Portfolio project report

## Skills Demonstrated

- FMEA and causal-chain analysis
- Functional safety reasoning
- Requirements and traceability
- AI governance
- YAML / JSON
- GitHub Actions
- Engineering review and RPN screening

## Portfolio Website

https://aparna3498.github.io/safestop-fmea-pipeline/

## Disclaimer

This project is a fictional documentation and simulation exercise for portfolio purposes only.

It does not verify a real machine, determine SIL/PL, prove standards compliance, provide certification evidence or replace human safety assessment.
