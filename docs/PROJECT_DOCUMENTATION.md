# SafeStop AI-FMEA Pipeline — Simple Guide

[Back to the project overview](../README.md)

## What is this tool?

SafeStop helps prepare a first draft of a **Failure Mode and Effects Analysis
(FMEA)** for a fictional robot emergency-stop system.

It takes a written system description, asks Gemini for possible failures,
checks the structure of the answer and creates reports for engineering review.
An engineer then checks each failure mechanism, effect and proposed detection.

The **API** is the connection between the Python program and Gemini. An
**API key** gives the program access to the provider. **GitHub Actions** runs
the Python steps when you start a workflow. An **artifact** is the downloadable
ZIP containing the results of a run.

## What system does it analyze?

The fictional system contains:

- a two-channel emergency-stop button, `ESTOP-01`;
- a safety controller, `CTRL-01`;
- two outputs, `OUT-Q1` and `OUT-Q2`, controlling K1 and K2;
- two series contactors, `K1` and `K2`;
- contactor feedback, `EDM-01`;
- manual reset, `RESET-01`;
- a 24 V control supply, `SUP-01`.

The intended safety function is: an emergency-stop demand on either channel
causes both outputs to de-energize, both contactors to open and motion-enabling
power to be removed. Restart remains inhibited until the required healthy
conditions and deliberate reset are present. Reset itself must not start motion.

Assumption `A-006` says either series contactor opening removes drive power.
That matters when reviewing a suggested failure such as one welded contactor.
Removing drive power alone does not prove hazardous motion has ceased.

The model excludes braking, stored energy, guarding, safety networks and
controller internals. Several assumptions still need verification; the safety
requirements are drafts. The 100 ms and 500 ms targets are illustrative.

## What files go into generation?

| File | Plain meaning |
| --- | --- |
| [system.yaml](../data/system.yaml) | What the system contains and how it should work |
| [assumptions.yaml](../data/assumptions.yaml) | Conditions assumed for the analysis and what needs checking |
| [requirements.yaml](../data/requirements.yaml) | Draft safety behavior and expected verification evidence |
| [fmea_prompt.md](../prompts/fmea_prompt.md) | Instructions telling the AI what to generate and what claims to avoid |

Python validates the YAML inputs, combines these four files with an output
schema and sends one generation request to Gemini. Reference answers, earlier
trial candidates and human review decisions are excluded from that request.

The response is saved as JSON: a structured text format the validation and
report code can read.

## What changed with the API?

| Stage | Existing capability | Added API capability |
| --- | --- | --- |
| Starting point | An already-created candidate JSON file | System evidence and generation instructions |
| Generation | Performed outside the report code | Python requests draft candidates directly from Gemini |
| Checking and reporting | Validate JSON and build reports | Run those steps after generation |
| Run record | Committed trial data | Additional metadata for the API generation |

The integration is implemented and has passed connection and full-generation
checks. Technical review of the generated content is a separate step.

## Choose the right workflow

| Workflow | What it does | Calls Gemini? |
| --- | --- | --- |
| **Validate safety inputs** | Checks code, evidence, schema and committed TRIAL-01 data on pushes and pull requests; also supports a manual run | No |
| **Build FMEA report** | Creates reports from `trials/<trial_id>/fmea_candidates.json` already in the repository | No |
| **Generate FMEA with Gemini** — `connection-test` | Sends a small request to check provider access; creates no FMEA files | Yes, once |
| **Generate FMEA with Gemini** — `generate` | Generates and validates new candidates, then creates reports | Yes, once |

The report workflow lists TRIAL-01, TRIAL-02 and TRIAL-03, but a selected trial
must have a candidate file committed in that location. An API artifact does
not automatically create a saved trial in the repository.

## Generate on GitHub

### Set up the key once

Skip this step if the repository already has `GEMINI_API_KEY` configured.

1. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey).
2. In GitHub, open **Settings → Secrets and variables → Actions**.
3. Select **New repository secret**, name it `GEMINI_API_KEY` and enter the key.

Keep credentials out of code, documentation and messages. For free-tier use,
check the project's eligibility and quota and keep paid billing disabled. The
program cannot inspect billing settings. Check Google's current
[pricing](https://ai.google.dev/gemini-api/docs/pricing),
[rate limits](https://ai.google.dev/gemini-api/docs/rate-limits) and data terms
before using the service or sending confidential information.

### Check access, then generate

1. Open **Actions → Generate FMEA with Gemini → Run workflow**.
2. Select branch `main`, mode `connection-test` and start the run.
3. A successful connection test confirms the small request worked. It does not test the full FMEA output or create an artifact.
4. Open **Run workflow** again, choose mode `generate`, select a trial label and start it.
5. Open the successful run and download its ZIP from **Artifacts**.

Once access is confirmed, future generation runs can start in `generate` mode.
To change mode, start a new **Run workflow**. **Re-run all jobs** retains the
previous run's inputs, including its mode.

### Read the results

| Generated file | Purpose |
| --- | --- |
| `fmea_candidates.json` | Original structured AI candidates |
| `fmea_candidates.metadata.json` | Requested model, UTC timestamp, elapsed time, candidate count, hashes and available provider usage/ID |
| `fmea_report.md` | Readable Markdown report |
| `fmea_report.xlsx` | Workbook for engineering review |

A **hash** is a file fingerprint. Comparing hashes helps establish whether the
inputs or saved output changed. Metadata supports tracing a run; it does not
guarantee identical answers on a later run. Provider fields may be absent or null.

Each API artifact name includes the trial label, run ID and attempt number.
Artifacts are retained for 30 days. Download and retain the evidence needed for
comparison. The workflow does not commit generated files or review decisions.

## What does Python check?

| Automatic check | What it establishes |
| --- | --- |
| Input structure and linked IDs | YAML follows the expected structure and uses known links |
| Candidate fields, types and allowed labels | JSON follows the defined candidate contract |
| Sequential candidate IDs | Candidate numbering has no gaps |
| Element and evidence IDs | References use supplied IDs, including at least one assumption or requirement per candidate |
| Repeated element/failure-mode text | Exact duplicates after case and whitespace normalization are flagged |
| Defined prohibited-claim patterns | Certain SIL, PL, certification and compliance phrases are flagged |

These checks do not establish whether a cited requirement supports the claim,
whether the causal chain is correct, or whether every important failure was
found. Reworded duplicates and unsupported engineering statements can pass.

## What does the engineer review?

For each candidate:

1. Check that the failure mechanism is distinct and physically credible.
2. Follow its local effect through to the safety-function effect.
3. Check whether diagnostics and evidence references support the statements.
4. Record corrections, uncertainty and missing evidence.
5. Accept, revise or reject the draft through the review process.
6. Retain independent verification evidence for any engineering conclusions.

The generated Excel workbook has three sheets: **Summary**, **Rating Criteria**
and **FMEA Candidates**. It includes editable review fields. Severity (S),
Occurrence (O) and Detectability (D) are left blank for human input.

The 1–10 rating criteria are illustrative portfolio placeholders. RPN is
calculated as `S × O × D` only after all three values are entered. No acceptance
threshold is defined; RPN does not approve safety. AI confidence and screening
labels are also not engineering risk ratings.

## What has been demonstrated?

| Trial | Recorded evidence | Limits of the result |
| --- | --- | --- |
| [TRIAL-01](../trials/TRIAL-01/fmea_candidates.json) | 29 ChatGPT-generated draft candidates stored in the repository | Not an independently validated reference FMEA |
| [TRIAL-02](https://github.com/Aparna3498/safestop-fmea-pipeline/actions/runs/40691511126), 2026-10-28 | 6 Gemini-generated draft candidates; recorded generation elapsed time 8.34 seconds; validation and both report builds passed | Demonstrates a working pipeline, not verified technical correctness or complete failure coverage |

The candidate counts and one run's elapsed time are observations, not a
quality comparison or performance benchmark. The trials used different
generation setups. A fair comparison needs controlled conditions and recorded
engineering review against an independently established reference.

Any portfolio reference-mapping figures remain draft AI-assisted assessments
pending human confirmation. Neither another AI output nor a software pass is
independent verification evidence.

## Run locally

Use Python 3.12 and run commands from the repository folder.

### Install and check without an API key

```bash
python -m pip install -r requirements.txt
python src/validate_inputs.py
python -m src.export_schema --check
python -m unittest discover -s tests -v
python -m src.generate_candidates --dry-run --output outputs/API-CHECK/fmea_candidates.json
```

The dry run validates the evidence and builds the request in memory. It makes
no API call and writes no candidate file.

### Build reports from the saved trial

```bash
python -m src.validate_candidates trials/TRIAL-01/fmea_candidates.json
python -m src.render_report trials/TRIAL-01/fmea_candidates.json --trial-id TRIAL-01 --output outputs/TRIAL-01/fmea_report.md
python -m src.render_xlsx trials/TRIAL-01/fmea_candidates.json --trial-id TRIAL-01 --output outputs/TRIAL-01/fmea_report.xlsx
```

### Call Gemini locally

Set `GEMINI_API_KEY` securely in your shell environment before running these
commands. Do not put a real key into a script or tracked file.

```bash
python -m src.generate_candidates --connection-test
python -m src.generate_candidates --output outputs/TRIAL-02/fmea_candidates.json
python -m src.validate_candidates outputs/TRIAL-02/fmea_candidates.json
python -m src.render_report outputs/TRIAL-02/fmea_candidates.json --trial-id TRIAL-02 --output outputs/TRIAL-02/fmea_report.md
python -m src.render_xlsx outputs/TRIAL-02/fmea_candidates.json --trial-id TRIAL-02 --output outputs/TRIAL-02/fmea_report.xlsx
```

Choose a new directory for each local generation. Generation refuses to replace
an existing candidate file or metadata file. The report commands create files
locally; GitHub uploads artifacts only when its workflow is used.

## API behavior and troubleshooting

The configured model is `gemini-3.5-flash-lite` in
[generate_candidates.py](../src/generate_candidates.py). It uses the Gemini
Interactions REST endpoint with structured JSON output and `store: false`.
The small connection test has a 60-second socket timeout; generation has a
300-second socket timeout. The GitHub generation job is limited to 10 minutes.

Each mode attempts at most one API request, with no automatic retry or fallback
to another model. Push and pull-request checks make no API calls. The program
does not print credentials or raw provider error bodies.

| What you see | Meaning or next step |
| --- | --- |
| Connection test succeeds but no report appears | Expected: start a new run in `generate` mode |
| Missing `GEMINI_API_KEY` | Configure the repository secret or local environment variable |
| HTTP 401 or 403 | Check credentials, permissions and project/region eligibility |
| HTTP 404 | Check whether the configured model is available to the project |
| HTTP 429 | Quota or rate limit reached; check the provider's quota before another manual attempt |
| Timeout | The response did not arrive in time; the provider may still have processed the request. This alone does not prove the key is invalid |
| Output schema or candidate validation fails | The returned answer did not pass the defined checks; no candidate file is written |
| Local output already exists | Choose a fresh generation output directory |
| Build FMEA report cannot find TRIAL-02 | Download the API artifact, or separately commit a trial file before using the saved-trial workflow |

## Connection to taxonomy-guided HARA research

SafeStop provides experience with structured safety inputs, controlled LLM
requests, traceability, validation and review. Those skills can support a
taxonomy-guided HARA prototype.

SafeStop itself generates FMEA candidates for this fictional E-stop. It does
not implement FHA/DDI extraction, VDA 702 taxonomy integration, operational-
situation generation or comparison with an industrial HARA. Those require
their own implementation and evaluation; the six FMEA candidates are portfolio
results, not thesis findings.

## Remaining project work

- Record human review decisions and corrections for retained candidates.
- Establish an independently reviewed reference before claiming coverage or accuracy.
- Run controlled additional trials and compare omissions, additions and duplicates.
- Keep original generation evidence separate from reviewer changes and verification records.

This fictional portfolio exercise does not verify a real machine, assign
SIL/PL, demonstrate compliance or provide certification evidence.
