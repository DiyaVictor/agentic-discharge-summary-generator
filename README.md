# Agentic AI for Discharge Summaries

This repository contains the implementation of an Agentic AI system designed to ingest raw, messy clinical source notes (including admission logs, progress sheets, laboratory reports, and medication histories) and produce a structured, clinically safe discharge summary draft.

The system is designed with strict guardrails to prevent hallucination, reconcile medications, highlight conflicting data, and present missing information transparently for clinician review.

## Architecture & Loop Design

The agent is built using a state-machine loop configuration rather than a single direct LLM call or a loose, hardcoded pipeline. The loop executes through discrete phases and updates a single, versioned state object:

```
[ Ingestion ] ──> [ Demographics ] ──> [ Clinical Extraction ]
                                              │
[ Drafting ] <── [ Missing Data ] <── [ Med Reconciliation ] <── [ Escalation/Conflict ]
```

1. **Ingestion:** Reads raw clinical documents (mocked for ingestion simulation).
2. **Demographics Extraction:** Identifies demographics, admission dates, and weights.
3. **Clinical Course Extraction:** Compiles diagnoses, clinical course timelines, and tests.
4. **Escalation & Conflict Validation:** Validates identity and data consistency. In the sample dataset, it detects a critical mismatch: Pages 1-2 belong to a stable female patient with Acute Gastroenteritis, while Pages 3-71 belong to a male patient with Diabetic Ketoacidosis (DKA) who took discharge against medical advice. The agent logs this mismatch, triggers a clinician escalation alert, and proceeds using only the primary patient file (Pages 3-71) to ensure safety.
5. **Medication Reconciliation:** Comprehensively compares admission vs. discharge medications. Identifies discontinued medicines without documented clinical reasons and flags that the patient is being discharged without essential treatment (such as insulin or antibiotics) for their primary diagnoses.
6. **Missing Data Identification:** Flags any mandatory fields that cannot be verified in the documents, leaving them explicitly labeled as `[MISSING - CLINICIAN REVIEW REQUIRED]`.
7. **Draft Generation:** Renders a formatted markdown report alongside a structured JSON payload for downstream ingestion.

---

## Technical Guardrails Against Hallucination

* **Strict Pydantic Validation:** The agent state uses Pydantic model defaults (like `[MISSING - CLINICIAN REVIEW REQUIRED]`) for required elements. If a field is not found in the documents, it defaults to the placeholder rather than allowing the model to invent plausible values.
* **Deterministic Reconciliation:** Medication reconciliation is performed methodically to trace changes between admission, inpatient stay, and discharge.
* **Granular Sources & Citations:** Every extracted demographic detail, diagnosis, and medication lists its source page (e.g. `p. 16`) to allow instant clinician auditability.
* **Iterative Cap Control:** The agent loop enforces a hard step cap to prevent runaway execution or infinite loop cycles.

---

## Setup & Running the Project

Follow these instructions to set up the project locally and run the mock execution.

### Prerequisites
* Python 3.8 or higher installed on your system.

### 1. Create a Virtual Environment
Initialize a clean virtual environment to isolate the project dependencies:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
Install all package dependencies via pip:
```bash
pip install -r requirements.txt
```

### 3. Run the Agent
Run the project in simulation mode to verify end-to-end execution:
```bash
python main.py --mode mock
```

---

## Outputs Generated

After a successful run, the agent outputs are placed in the `output/` directory:

1. **`output/trace.log`**: Step-by-step trace showing the agent's internal reasoning, action selection, tool parameters, results, and subsequent state routing.
2. **`output/discharge_summary.json`**: The final structured data payload containing demographics, reconciled medications, diagnoses, and clinician alerts.
3. **`output/discharge_summary.md`**: A professional, human-readable draft summary of the clinical stay, clearly flagging warnings and errors.

---

## Project Structure

```
.
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── main.py
└── src/
    ├── __init__.py
    ├── agent.py
    ├── state.py
    ├── logger.py
    └── tools.py
```

## Part 2 Discussion (Future Improvements)

To elevate the agent beyond basic extraction:
* **Human-in-the-Loop Alignment (RLHF / DPO):** We can fine-tune extraction and summarization styles by collecting clinician revisions. Re-run training with Direct Preference Optimization (DPO) using paired `(original_draft, doctor_edited_draft)` data. This teaches the model the exact stylistic preferences of the medical staff, reducing manual revision overhead.
* **Multimodal Handwriting Ingestion:** Implement high-resolution Vision-Language Models (VLM) like Gemini 1.5 Pro to transcribe handwritten nursing charts and ICU flowchart logs.
