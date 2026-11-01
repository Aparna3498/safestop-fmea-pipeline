# SafeStop AI-FMEA Pipeline

SafeStop uses AI to draft an FMEA for a fictional robot emergency-stop system. Python checks the draft and creates reports for engineering review.

**FMEA means Failure Mode and Effects Analysis:** considering what could fail, what could happen as a result, and how the failure might be detected.

[Portfolio website](https://aparna3498.github.io/safestop-fmea-pipeline/) · [Detailed background and original TRIAL-01 workflow](docs/PROJECT_DOCUMENTATION.md)

## Start with the files

The input files tell the AI what system to analyse and which information it may use.

| File | What it contains |
| --- | --- |
| [data/system.yaml](data/system.yaml) | The system components, connections and analysis boundary |
| [data/assumptions.yaml](data/assumptions.yaml) | Conditions assumed to be true for this example |
| [data/requirements.yaml](data/requirements.yaml) | Draft safety requirements with IDs that candidates can refer to |
| [prompts/fmea_prompt.md](prompts/fmea_prompt.md) | Instructions for the AI, including the requested answer format and limits |
| [trials/TRIAL-01/fmea_candidates.json](trials/TRIAL-01/fmea_candidates.json) | A saved AI answer containing 29 preliminary FMEA candidates |

**YAML** organises the input information. **JSON** organises the AI answer so Python can read it. The candidate JSON is then passed to the report tools.

## What changed with the API integration

The input files already existed. The new part is Python code that reads them, asks Gemini for a fresh answer, and passes that answer to the checks and report tools.

| Part of the process | Earlier report workflow | Added Gemini workflow |
| --- | --- | --- |
| System information | Stored in the YAML files | Uses the same input files and prompt |
| Where the workflow starts | A candidate JSON file already saved in the repository | Python reads the inputs and requests new candidates from Gemini |
| AI generation | Described in the original documentation as an interactive ChatGPT step outside the report workflow | A Gemini API request made by the Python program |
| Candidate checks | Python checks the saved candidates | Python checks the newly returned candidates |
| Reports | Creates Markdown and Excel reports | Reuses the report tools after generation succeeds |

An **API** is a way for a program to request something from another service. Here, Python sends text to Gemini and receives an answer. An **API key** gives the program access to that service.

The earlier workflow already automated checking and reporting. The added API request lets the program obtain new candidates itself, instead of starting from an answer already saved in the repository.

### Where the change lives

[src/generate_candidates.py](src/generate_candidates.py) handles the request, response checks and saved results. [.github/workflows/generate-with-gemini.yml](.github/workflows/generate-with-gemini.yml) runs it from GitHub. The existing validators and report tools are reused.

## What happens when you generate a new draft

**GitHub Actions** runs Python on a GitHub computer when you click **Run workflow**.

1. Python checks the system, assumptions and requirements files.
2. It combines those files with the FMEA prompt and the required JSON format.
3. It sends one request to Gemini.
4. Gemini returns proposed failure modes and their associated FMEA information.
5. Python checks the structure, allowed IDs, traceability and other defined rules.
6. If the checks pass, the workflow creates downloadable JSON, Markdown and Excel files.
7. An engineer reviews the candidates, corrects the reasoning and records decisions.

For example, the AI might suggest a contactor welded closed. Its effect needs review: K1 and K2 are in series, and either opening is assumed to remove drive power.

Passing the software checks means the output meets the defined rules. It does not establish engineering correctness or complete failure coverage.

## Choose the workflow you need

| What you want to do | Workflow or mode | API key needed? |
| --- | --- | --- |
| Check the code and committed data | **Validate safety inputs** | No |
| Create reports from an existing saved trial | **Build FMEA report** | No |
| Check whether Gemini responds | **Generate FMEA with Gemini** → `connection-test` | Yes |
| Generate new candidates and reports | **Generate FMEA with Gemini** → `generate` | Yes |

### Connection test and generation are different

The connection test sends a tiny request asking Gemini to return `{"status":"ok"}`. Python checks the reply and prints whether the test passed. It creates no FMEA candidates or reports.

Generation sends the system evidence and FMEA instructions. It produces a draft that needs engineering review.

## Run it on GitHub

### One-time setup

If the repository already has `GEMINI_API_KEY` configured, continue to the run steps.

1. Create an API key in [Google AI Studio](https://aistudio.google.com/apikey).
2. Open **Settings → Secrets and variables → Actions → New repository secret**.
3. Name the secret `GEMINI_API_KEY` and enter the key as its value. Keep the key out of source files and chat messages.

For free-tier use, check your project's billing settings, [pricing](https://ai.google.dev/gemini-api/docs/pricing) and [quota](https://ai.google.dev/gemini-api/docs/rate-limits). The code cannot check your billing tier. Use the fictional inputs; check the provider's data terms before sending confidential information.

### Start a run and open the result

1. Open **Actions → Generate FMEA with Gemini → Run workflow** and select branch `main`.
2. Choose `connection-test` for the first access check.
3. Once it passes, open **Run workflow** again. Choose `generate` and a trial label such as `TRIAL-02`.
4. When generation succeeds, open the run summary and download the ZIP under **Artifacts**.
5. Extract it and open `fmea_report.xlsx` to review the draft.

Use **Run workflow** to choose different inputs. **Re-run all jobs** repeats the inputs from the earlier run.

An **artifact** is a downloadable bundle saved by the workflow:

| File | What you use it for |
| --- | --- |
| `fmea_candidates.json` | The structured AI draft used by the program |
| `fmea_candidates.metadata.json` | The requested model, timing, available usage details and file fingerprints for that run |
| `fmea_report.md` | A readable text report |
| `fmea_report.xlsx` | An editable workbook for engineering review |

Artifacts last 30 days. Download what you need; results are not committed to the repository automatically.

## What has been tested

Both of these runs succeeded on **28 October 2026**:

- [Gemini connection test](https://github.com/Aparna3498/safestop-fmea-pipeline/actions/runs/40690893460): the small API request and reply check passed.
- [TRIAL-02 generation](https://github.com/Aparna3498/safestop-fmea-pipeline/actions/runs/40691511126): generation, candidate checks, report creation and artifact upload passed.

TRIAL-01 remains a saved draft with 29 candidates. Neither candidate counts nor successful runs measure FMEA completeness. It is not ground truth for another trial.

## Check the setup locally without an API call

From the repository folder, using Python 3.12:

```bash
python -m pip install -r requirements.txt
python -m src.generate_candidates --dry-run --output outputs/API-CHECK/fmea_candidates.json
```

This checks the input evidence and request setup. It needs no key, makes no API request and writes no candidate file.

<details>
<summary>Local generation commands and technical details</summary>

Set `GEMINI_API_KEY` securely in your shell environment, then run:

```bash
python -m src.generate_candidates --connection-test

# After the connection test passes:
python -m src.generate_candidates --output outputs/TRIAL-02/fmea_candidates.json
python -m src.validate_candidates outputs/TRIAL-02/fmea_candidates.json
python -m src.render_report outputs/TRIAL-02/fmea_candidates.json --trial-id TRIAL-02 --output outputs/TRIAL-02/fmea_report.md
python -m src.render_xlsx outputs/TRIAL-02/fmea_candidates.json --trial-id TRIAL-02 --output outputs/TRIAL-02/fmea_report.xlsx
```

Use a fresh output directory for each local run. Existing candidate and metadata files are not overwritten.

The configured model and endpoint are in `src/generate_candidates.py`. Each manually started API run makes one request, with no automatic retries. The connection test has a 60-second socket timeout, generation has a 300-second socket timeout, and the GitHub job has a 10-minute limit. Push and pull-request validation makes no API calls.

Rejected responses produce no candidate file. A timeout does not prove the key is invalid, and the provider may still have processed the request. Use the connection test to check basic access.

Metadata records the requested model, timing, interaction ID, available usage and file hashes. A hash is a fingerprint for identifying a version, not a quality score.

</details>

## System and review boundary

The fictional emergency-stop function includes dual-channel E-stop inputs, a safety controller, outputs Q1/Q2, series contactors K1/K2, EDM feedback, manual reset and a 24 V control supply.

The AI proposes candidates. Engineers review the causal reasoning, assumptions, missing evidence and safety implications. Severity, Occurrence and Detectability ratings are entered by a human; the workbook calculates RPN after those entries.

This is a portfolio and learning exercise. It does not verify a real machine, establish SIL/PL or standards compliance, or provide certification evidence.

## Connection to the thesis

This project provides API and structured-output practice for the thesis. The thesis concerns taxonomy-guided generation and evaluation of automotive HARA situations; this FMEA exercise is a separate learning example.
