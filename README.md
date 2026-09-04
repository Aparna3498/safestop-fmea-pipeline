# SafeStop AI-FMEA Pipeline

SafeStop-AI explores how AI can support the first draft of an FMEA while keeping engineering review, correction and safety decisions under human control.

📘 **[Read the complete project documentation](docs/PROJECT_DOCUMENTATION.md)**

## Project Highlights

- Structured system, assumption and requirement evidence in YAML
- 29 preliminary AI-generated FMEA candidates in TRIAL-01
- Python checks for input structure, traceability, duplicate mechanisms and prohibited safety claims
- GitHub Actions-based validation and report generation
- Editable Excel workbook for human review, with illustrative S/O/D and RPN fields
- Explicit uncertainty, traceability and human-in-the-loop controls

## Workflow

1. Prepare controlled system evidence in YAML
2. Generate structured FMEA candidates using a controlled prompt
3. Validate the candidate JSON using Python and GitHub Actions
4. Generate Markdown and Excel review reports
5. Perform human review and illustrative S/O/D-RPN screening
6. Record corrections and retain independent verification evidence outside the AI output

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
