# SafeStop AI-FMEA Pipeline

**Describe a system, ask Gemini what could go wrong, and create a draft FMEA report for an engineer to review.**

FMEA means *Failure Mode and Effects Analysis*: looking at possible failures,
their effects, and how they could be detected. This project uses a fictional
industrial robot emergency-stop system.

[Full guide](docs/PROJECT_DOCUMENTATION.md) · [Portfolio website](https://aparna3498.github.io/safestop-fmea-pipeline/)

## What the tool does

When you start **Generate FMEA with Gemini** in `generate` mode:

1. Python reads the system description, assumptions, draft safety requirements and FMEA prompt.
2. It sends those inputs to Gemini through an **API**: a connection that lets one program request an answer from another service.
3. Gemini returns draft failure modes, effects, detection ideas and suggested review actions.
4. Python checks the response format, allowed IDs and other defined rules.
5. GitHub Actions provides JSON, Markdown and Excel files to download.
6. An engineer checks the reasoning, corrects the candidates and records review decisions.

For example, Gemini may suggest **a contactor welded closed**. The engineer
must check what that means for this architecture: K1 and K2 are in series, so
the other contactor opening is assumed to remove drive power.

**A successful software check means the output passed the defined rules.
Engineering correctness and completeness still require review.**

## What the API integration added

| Earlier capability | Added capability |
| --- | --- |
| Check an existing candidate JSON file and build reports | Ask Gemini to generate candidates, then check them and build reports |

The API integration is implemented and has passed a live generation run.
The existing report workflow is also available. Starting a new generation
does not require copying prompts or AI answers between applications.

## Choose what you want to do

| Your goal | GitHub Actions workflow | API key needed? |
| --- | --- | --- |
| Check the code and committed data | **Validate safety inputs** | No |
| Build reports from a saved trial, such as TRIAL-01 | **Build FMEA report** | No |
| Check whether Gemini responds | **Generate FMEA with Gemini**, mode `connection-test` | Yes |
| Generate a new FMEA draft and reports | **Generate FMEA with Gemini**, mode `generate` | Yes |

## Generate a new draft on GitHub

### One-time setup

If `GEMINI_API_KEY` is already configured, skip this setup.

1. Create a key in [Google AI Studio](https://aistudio.google.com/apikey).
2. In your repository, open **Settings → Secrets and variables → Actions → New repository secret**.
3. Name the secret `GEMINI_API_KEY` and enter the key as its value. Keep the key out of source files and chat messages.

For free-tier use, check your project's eligibility and quota and keep paid
billing disabled. See Google's [pricing](https://ai.google.dev/gemini-api/docs/pricing)
and [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits).
The code cannot check your billing tier. Use the fictional project inputs;
check the provider's data terms before submitting confidential information.

### Run and download

1. Open **Actions → Generate FMEA with Gemini → Run workflow** and select branch `main`.
2. For the first access check, choose `connection-test`. A successful test creates no FMEA or report files.
3. To generate candidates, open **Run workflow** again and choose mode `generate` and a trial label, such as `TRIAL-02`.
4. When the run succeeds, open its summary and download the ZIP under **Artifacts**.
5. Open `fmea_report.xlsx` to begin engineering review.

Use **Run workflow** to change the mode. **Re-run all jobs** repeats the old inputs.
If access is already confirmed, you can go directly to `generate`.

The generation ZIP contains:

| File | What it is for |
| --- | --- |
| `fmea_candidates.json` | Structured AI draft used by the code |
| `fmea_candidates.metadata.json` | Model, timing, file fingerprints and available usage details |
| `fmea_report.md` | Readable text report |
| `fmea_report.xlsx` | Editable workbook for human review |

Artifacts are retained for 30 days. The workflow does not commit them to the
repository; download and retain any evidence you need.

## Recorded trials

| Trial | Recorded output | Meaning |
| --- | --- | --- |
| [TRIAL-01](trials/TRIAL-01/fmea_candidates.json) | 29 preliminary candidates | Existing ChatGPT-generated trial stored in the repository |
| [TRIAL-02 API run](https://github.com/Aparna3498/safestop-fmea-pipeline/actions/runs/40691511126) | 6 preliminary candidates; recorded generation time 8.34 seconds | Gemini generation, validation and report creation succeeded on 2026-10-28 |

Candidate counts do not measure quality or coverage. These trials are not
independently validated FMEAs, and TRIAL-01 is not ground truth for TRIAL-02.

## Check the setup locally without calling Gemini

Run these commands from the repository folder with Python 3.12:

```bash
python -m pip install -r requirements.txt
python -m src.generate_candidates --dry-run --output outputs/API-CHECK/fmea_candidates.json
```

This checks the evidence and request setup. It needs no key, makes no API call
and writes no candidate file. More commands and troubleshooting are in the
[full guide](docs/PROJECT_DOCUMENTATION.md#run-locally).

## Project boundary

This is a fictional portfolio exercise. AI proposes candidates; engineers
control corrections, S/O/D ratings and final decisions. The project does not
verify a real machine or provide SIL/PL, compliance or certification evidence.
