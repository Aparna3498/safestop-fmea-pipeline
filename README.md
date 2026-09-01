# SafeStop AI-FMEA Pipeline

A human-in-the-loop AI pipeline for generating and evaluating preliminary FMEA candidates for a fictional industrial robot emergency-stop system.

## Project objective

This project demonstrates how a Large Language Model can support preliminary Failure Mode and Effects Analysis without replacing the safety engineer.

The pipeline will:

1. Read a structured system description, assumptions and safety requirements.
2. Generate candidate failure modes using an LLM.
3. Validate the AI output against a defined JSON schema.
4. Detect unsupported elements, missing evidence references and duplicate candidates.
5. Compare the candidates with a human-created reference FMEA.
6. Generate coverage and quality metrics for human review.

## Example system

The example is a fictional fixed industrial robot cell containing:

- Dual-channel emergency-stop input
- Safety controller
- Two independent safety outputs
- Two series power contactors
- External device monitoring
- Manual reset
- 24 V control supply

## Safety position

The AI output is used only to generate candidates for human review.

It does not:

- Approve an FMEA
- Demonstrate functional-safety compliance
- Assign SIL or PL
- Replace verification or validation evidence
- Make final safety decisions

## Project status

Day 1 — Repository and input-data preparation.
