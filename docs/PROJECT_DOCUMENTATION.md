# SafeStop AI-FMEA Pipeline

SafeStop generates preliminary Failure Mode and Effects Analysis (FMEA) candidates for a fictional industrial robot emergency-stop system. Structured system information and a controlled prompt are sent to Gemini. Python checks the response and produces Markdown and Excel reports for engineering review.

[Project overview](../README.md) · [Portfolio website](https://aparna3498.github.io/safestop-fmea-pipeline/)

## System scope

The example models an emergency-stop function with two input channels, a safety controller, two outputs, series contactors, feedback monitoring and manual reset.

| Element | Role |
| --- | --- |
| `ESTOP-01`, `CH-A`, `CH-B` | Emergency-stop demand and input channels |
| `CTRL-01` | Input monitoring, output control and reset logic |
| `Q1`, `Q2` | Safety outputs and associated wiring |
| `K1`, `K2` | Series contactors in the drive-power path |
| `EDM-01` | Contactor feedback monitoring |
| `RESET-01`, `SUP-01` | Manual reset and 24 V control supply |

Assumption `A-006` states that either K1 or K2 opening is sufficient to remove power enabling hazardous motion. This assumption affects the interpretation of individual contactor faults. The model does not establish the behaviour of a real installation.

## Input evidence

| File | Contents |
| --- | --- |
| [system.yaml](../data/system.yaml) | Safety function, components, interfaces and analysis boundary |
| [assumptions.yaml](../data/assumptions.yaml) | Assumptions, rationale and confirmation status |
| [requirements.yaml](../data/requirements.yaml) | Draft safety requirements and verification expectations |
| [fmea_prompt.md](../prompts/fmea_prompt.md) | Generation instructions, required reasoning and output constraints |

Stable element, assumption and requirement IDs connect the inputs to the candidates. Only these evidence files and the prompt are included in the generation request; a reference FMEA is not supplied as an expected answer.

## Generation and validation

1. **Validate inputs.** Check the YAML structure, identifiers and links.
2. **Build the request.** Combine the evidence, prompt, allowed IDs and required JSON schema.
3. **Call Gemini.** Make one API request using `GEMINI_API_KEY`.
4. **Read the response.** Require completed, non-empty text output and parse the candidate object.
5. **Check candidates.** Apply the typed data contract and the defined consistency rules.
6. **Save results.** Write the accepted candidate array and run metadata, then render review reports.

The API response contains a `candidates` array. The saved `fmea_candidates.json` contains that array directly, which is the format consumed by the report tools.

The implementation is in [generate_candidates.py](../src/generate_candidates.py). The configured model and endpoint are defined there. Generation uses the existing [candidate validator](../src/validate_candidates.py) and report renderers.

### Candidate information

| Group | Fields |
| --- | --- |
| Identity | `candidate_id`, `element_id` |
| Failure and effects | `failure_mode`, `local_effect`, `system_effect`, `hazardous_consequence` |
| Detection and action | `detection_mechanism`, `recommended_action` |
| Traceability | `evidence_references` |
| Uncertainty | `confidence`, `assumptions`, `missing_information` |
| AI screening | `ai_classification` |

The contract is defined in [fmea_models.py](../src/fmea_models.py), with an exported [JSON schema](../schemas/fmea_candidates.schema.json).

Checks include:

- Sequential candidate IDs and valid boundary element IDs.
- Recognised evidence references, including at least one assumption or requirement reference.
- Required fields, allowed labels and rejection of unexpected fields.
- Duplicate element/failure-mode text after case and whitespace normalisation.
- Pattern checks for prohibited SIL, PL, certification and compliance claims.

These checks screen the output. They do not verify that a cited source supports a statement, detect every semantic duplicate, or prove that the causal reasoning is correct.

## Reports and review

| Output | Purpose |
| --- | --- |
| `fmea_candidates.json` | Structured candidates accepted by the software checks |
| `fmea_candidates.metadata.json` | Requested model, timing, available usage details and input/request/output hashes |
| `fmea_report.md` | Readable review report |
| `fmea_report.xlsx` | Editable review workbook |

The Excel workbook contains **Summary**, **Rating Criteria** and **FMEA Candidates** sheets. Reviewers enter Severity, Occurrence and Detectability ratings, dispositions, corrections and notes. RPN is calculated only after all three ratings are entered.

The supplied rating scale is illustrative. No approved RPN acceptance threshold is defined. AI screening labels such as "Safe" or "Dangerous" and the confidence labels are proposals for review, not engineering verdicts.

Review should establish whether each mechanism is distinct, whether the local and system effects follow from the architecture, and which assumptions or missing evidence need resolution.

## Running the project

### GitHub Actions

| Workflow | Function | API key |
| --- | --- | --- |
| **Validate safety inputs** | Checks code and committed evidence on pushes and pull requests | Not required |
| **Build FMEA report** | Validates a saved trial and builds reports | Not required |
| **Generate FMEA with Gemini** | Tests API access or generates new candidates and reports | Required |

Add `GEMINI_API_KEY` as an Actions secret in a repository you control. Open **Actions → Generate FMEA with Gemini → Run workflow**.

Use `connection-test` for a small access check. It asks for `{"status":"ok"}` and creates no FMEA files. Start a new run in `generate` mode to request candidates. Download the resulting ZIP from **Artifacts**.

Artifacts are retained for 30 days. They are not committed automatically. The API workflow makes one request per manual run, with no automatic retries. API access, billing and quota depend on the configured Google project.

### Local execution

Use Python 3.12 and install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Check the request setup without an API call:

```bash
python -m src.generate_candidates --dry-run --output outputs/API-CHECK/fmea_candidates.json
```

With `GEMINI_API_KEY` set securely in the environment:

```bash
python -m src.generate_candidates --connection-test
python -m src.generate_candidates --output outputs/TRIAL-02/fmea_candidates.json
python -m src.validate_candidates outputs/TRIAL-02/fmea_candidates.json
python -m src.render_report outputs/TRIAL-02/fmea_candidates.json --trial-id TRIAL-02 --output outputs/TRIAL-02/fmea_report.md
python -m src.render_xlsx outputs/TRIAL-02/fmea_candidates.json --trial-id TRIAL-02 --output outputs/TRIAL-02/fmea_report.xlsx
```

Use a fresh output directory for each generation run. Existing candidate and metadata files are not overwritten.

The connection-test socket timeout is 60 seconds; generation allows 300 seconds. The GitHub job limit is 10 minutes. A timeout does not establish whether the provider processed the request. Rejected or incomplete responses produce no candidate file.

## Recorded evidence

| Record | What it demonstrates |
| --- | --- |
| [Saved TRIAL-01](../trials/TRIAL-01/fmea_candidates.json) | 29 preliminary candidates stored for review and report generation |
| [Connection test on 28 October 2026](https://github.com/Aparna3498/safestop-fmea-pipeline/actions/runs/40690893460) | API access and the expected reply check passed |
| [TRIAL-02 generation on 28 October 2026](https://github.com/Aparna3498/safestop-fmea-pipeline/actions/runs/40691511126) | Generation, candidate checks, Markdown/Excel rendering and artifact upload passed |

These records demonstrate implemented software behaviour. They do not establish independent FMEA quality, reference coverage or completeness.

## Limitations

The system is fictional and simplified, and architecture assumptions require confirmation before any real application. The project does not provide verified schematics, component data or machine test evidence.

Engineering review remains necessary for the reasoning, coverage, ratings and final decisions. The outputs do not verify a real machine or establish SIL/PL, standards compliance or certification.
