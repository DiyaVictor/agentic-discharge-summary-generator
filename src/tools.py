import os
from src.state import AgentState

def mock_pdf_ingestion(file_path: str, use_vlm_for_handwriting: bool) -> str:
    """Mock document ingestion and OCR."""
    return "Successfully extracted text and structured tables from 71 pages."

def mock_extract_demographics() -> dict:
    """Mock extraction of demographics information."""
    return {
        "name": "[MISSING - CLINICIAN REVIEW REQUIRED]",
        "age": "[MISSING - CLINICIAN REVIEW REQUIRED]",
        "gender": "[CONFLICT DETECTED - CLINICIAN REVIEW REQUIRED]",
        "weight": "71 kg",
        "sources": ["p. 1", "p. 16", "p. 42", "p. 43", "p. 44", "p. 45", "p. 46"]
    }

def mock_extract_clinical_course() -> dict:
    """Mock extraction of clinical diagnoses and hospital course."""
    return {
        "admission_date": "26/02/2026",
        "discharge_date": "02/03/2026",
        "diagnoses": {
            "principal": [
                "Diabetic Ketoacidosis (DKA)",
                "Uncontrolled Type 2 Diabetes Mellitus (T2DM)"
            ],
            "secondary": [
                "Acute Febrile Illness (AFI)",
                "Bilateral Pyelonephritis",
                "Acute Kidney Injury (AKI)",
                "Cholelithiasis without cholecystitis",
                "? Synovitis"
            ],
            "conflicts": [
                "Page 1 lists Acute Gastroenteritis with Dehydration and Urinary Tract Infection"
            ],
            "sources": ["p. 1", "p. 3", "p. 30", "p. 41", "p. 42", "p. 43", "p. 44", "p. 46", "p. 48", "p. 49", "p. 51", "p. 54", "p. 56", "p. 57", "p. 58"]
        },
        "hospital_course": [
            "Presented to ER on 26/02/2026 with fever, generalized weakness for 3 days, and myalgia.",
            "Known case of T2DM on Ayurvedic medication.",
            "In ER, hypotensive (BP 87/50 mmHg) with GRBS of 443 mg/dL and diagnosed with DKA. Treated with IV fluids, IV Pantoprazole, and IV Emeset.",
            "Admitted to HDU/ICU for further management.",
            "Managed with IV fluids, Human Actrapid insulin infusion, Lantus, IV Meropenem (Meromac), IV Pantoprazole, and IV Emeset.",
            "Imaging (USG Abdomen & Pelvis, CT KUB Plain) revealed bilateral pyelonephritis, cholelithiasis, minimal ascites, and minimal right pleural effusion.",
            "Urology opinion obtained.",
            "Orthopedics consulted for right hip/leg pain, advised X-ray pelvis, and prescribed T. Ultracet and T. Etoshine.",
            "Dietician counseling provided.",
            "Patient requested discharge against medical advice / on request on 02/03/2026."
        ],
        "procedures": [
            "IV Cannulation",
            "Foley's Catheterization",
            "CT KUB Plain",
            "USG Abdomen & Pelvis",
            "2D Echo",
            "ECG"
        ],
        "allergies": "Not known",
        "discharge_condition": {
            "status": "Conscious, oriented. Discharged on request (Evening).",
            "vitals": "BP 170/80 mmHg, SpO2 97%, HR 110 b/m",
            "sources": ["p. 56"]
        }
    }

def mock_escalate_to_clinician(reason: str) -> str:
    """Mock escalation process when record mismatch or safety issues are found."""
    return "Escalation logged. State updated to isolate Pages 1-2 as invalid but flagged for review."

def mock_medication_reconciliation() -> dict:
    """Mock medication reconciliation."""
    return {
        "admission": [
            "Ayurvedic medication for T2DM"
        ],
        "discharge": [
            "T. Ultracet 1-0-1 for 5 days",
            "T. Etoshine 90mg 1-0-0"
        ],
        "reconciliation_flags": [
            "Ayurvedic medication stopped without documented reason.",
            "Discharge medications for primary conditions (DKA, T2DM, Pyelonephritis) are missing.",
            "Page 2 discharge medications conflict with clinical course."
        ],
        "sources": ["p. 2", "p. 46", "p. 57"]
    }

def mock_check_missing_data() -> dict:
    """Mock check for missing required fields and pending lab results."""
    return {
        "follow_up_instructions": "[MISSING - CLINICIAN REVIEW REQUIRED]",
        "pending_results": [
            "Blood Culture",
            "X-ray Pelvis"
        ],
        "clinician_review_required": {
            "safety_concerns": [
                "Patient Record Mix-Up: Pages 1-2 belong to a different patient.",
                "Unsafe Discharge Plan: No insulin or antibiotics prescribed at discharge for DKA/Pyelonephritis patient."
            ],
            "missing_information": [
                "Patient Name",
                "Patient Age",
                "Follow-up Instructions"
            ]
        }
    }

def generate_markdown_draft(state: AgentState, output_path: str) -> None:
    """Generates the Markdown report draft from the AgentState."""
    md_content = f"""# DISCHARGE SUMMARY (DRAFT)

**WARNING: [CONFLICT DETECTED - CLINICIAN REVIEW REQUIRED]**
*Multiple critical contradictions detected in source documents. Pages 1-2 appear to belong to a different patient record (Female, Gastroenteritis) than Pages 3-71 (Male, DKA, Pyelonephritis). This draft isolates facts from the primary clinical course (Pages 3-71) but requires immediate clinician verification.*

## Patient Demographics
* **Name:** {state.patient_demographics.name}
* **Age:** {state.patient_demographics.age}
* **Gender:** {state.patient_demographics.gender} (Source: "she" on p. 1 vs. "his" on p. 46)
* **Weight:** {state.patient_demographics.weight} (Source: p. 16, 42, 43, 44, 45)

## Admission & Discharge Dates
* **Admission Date:** {state.admission_date} (Source: p. 3, 16, 17, 37, 46)
* **Discharge Date:** {state.discharge_date} (Source: p. 56)

## Diagnoses
* **Principal Diagnoses:** 
"""
    for diag in state.diagnoses.principal:
        md_content += f"  * {diag} (Source: p. 3, 43, 44, 54, 56, 58)\n"
    for conflict in state.diagnoses.conflicts:
        md_content += f"  * *[CONFLICT DETECTED - CLINICIAN REVIEW REQUIRED]: {conflict}*\n"
        
    md_content += "* **Secondary Diagnoses:** \n"
    for diag in state.diagnoses.secondary:
        if diag == "Acute Febrile Illness (AFI)":
            md_content += f"  * {diag} (Source: p. 42, 44, 54, 56, 58)\n"
        elif diag == "Bilateral Pyelonephritis":
            md_content += f"  * {diag} (Source: p. 30, 41, 51, 54, 56, 58)\n"
        elif diag == "Acute Kidney Injury (AKI)":
            md_content += f"  * {diag} (Source: p. 49)\n"
        elif diag == "Cholelithiasis without cholecystitis":
            md_content += f"  * {diag} (Source: p. 30, 41, 48)\n"
        elif diag == "? Synovitis":
            md_content += f"  * {diag} (Source: p. 48, 57)\n"
        else:
            md_content += f"  * {diag}\n"
            
    md_content += "  * *[CONFLICT DETECTED - CLINICIAN REVIEW REQUIRED]: Page 1 lists \"Urinary Tract Infection\"*\n"

    md_content += "\n## Hospital Course\n"
    for idx, course_item in enumerate(state.hospital_course):
        if "Presented to ER" in course_item:
            md_content += f"* {course_item[:-1]} (Source: p. 16, 46).\n"
        elif "Ayurvedic" in course_item:
            md_content += f"* {course_item[:-1]} (Source: p. 46).\n"
        elif "In ER" in course_item:
            md_content += f"* In ER, patient was hypotensive (BP 87/50 mmHg) with GRBS of 443 mg/dL and diagnosed with DKA (Source: p. 3, 16). Treated with IV fluids (NS bolus), IV Pantoprazole, and IV Emeset (Source: p. 4).\n"
        elif "Admitted to HDU" in course_item:
            md_content += f"* {course_item[:-1]} (Source: p. 17, 64).\n"
        elif "Managed with IV fluids" in course_item:
            md_content += f"* Managed with IV fluids, Human Actrapid insulin infusion, Lantus, IV Meropenem (Meromac), IV Pantoprazole, and IV Emeset (Source: p. 37-39, 42-44).\n"
        elif "Imaging" in course_item:
            md_content += f"* Imaging including USG Abdomen & Pelvis (Source: p. 30) and CT KUB Plain (Source: p. 41) revealed bilateral pyelonephritis, cholelithiasis, minimal ascites, and minimal right pleural effusion.\n"
        elif "Urology opinion" in course_item:
            md_content += f"* Urology opinion was obtained (Source: p. 51, 52).\n"
        elif "Orthopedics" in course_item:
            md_content += f"* Orthopedics consulted for right hip/leg pain, advised X-ray pelvis, and prescribed T. Ultracet and T. Etoshine (Source: p. 57).\n"
        elif "Dietician" in course_item:
            md_content += f"* Dietician counseling was provided (Source: p. 58).\n"
        elif "discharged against medical advice" in course_item:
            md_content += f"* Patient requested discharge against medical advice / on request on 02/03/2026 (Source: p. 56).\n"
        else:
            md_content += f"* {course_item}\n"

    md_content += "\n## Procedures\n"
    for proc in state.procedures:
        if proc == "IV Cannulation":
            md_content += f"* {proc} (Source: p. 3, 15, 17)\n"
        elif proc == "Foley's Catheterization":
            md_content += f"* {proc} (Source: p. 15, 26 - removed 01/03/2026)\n"
        elif proc == "CT KUB Plain":
            md_content += f"* {proc} (Source: p. 41)\n"
        elif proc == "USG Abdomen & Pelvis":
            md_content += f"* {proc} (Source: p. 30)\n"
        elif proc == "2D Echo":
            md_content += f"* {proc} (Source: p. 32, 50)\n"
        elif proc == "ECG":
            md_content += f"* {proc} (Source: p. 17, 30)\n"
        else:
            md_content += f"* {proc}\n"

    md_content += f"""
## Medications
* **Admission Medications:** {state.medications.admission[0]} (Source: p. 46)
* **Discharge Medications:** 
  * T. Ultracet 1-0-1 for 5 days (Source: p. 57)
  * T. Etoshine 90mg 1-0-0 (Source: p. 57)
  * *[MISSING - CLINICIAN REVIEW REQUIRED]: Discharge medications for primary conditions (DKA, T2DM, Pyelonephritis) are not documented.*
  * *[CONFLICT DETECTED - CLINICIAN REVIEW REQUIRED]: Page 2 lists Raciper, Emeset, Oflox TZ, M Strong, Zedott, Entro, Meftal Spas, Loperamide. These do not match the clinical course.*

## Allergies
* {state.allergies} (Source: p. 17, 42, 43, 44, 46, 49)

## Follow-up Instructions
* {state.follow_up_instructions} (Source: No follow-up plan documented in valid notes prior to discharge on request).

## Pending Results
* Blood Culture (Source: p. 69, 70 - ordered, report not in file)
* X-ray Pelvis (Source: p. 57 - advised, report not in file)

## Discharge Condition
* {state.discharge_condition.status[:-1]} (Source: p. 56)
* Vitals at discharge: {state.discharge_condition.vitals} (Source: p. 56)
* {state.discharge_condition.status.split(". ")[1]} (Source: p. 56)

---

# CLINICIAN REVIEW REQUIRED

### 🚨 Critical Safety Concerns
* **Patient Record Mix-Up:** Pages 1 and 2 of the provided file belong to a different patient. They describe a female patient treated for Acute Gastroenteritis and UTI, discharged hemodynamically stable with oral antibiotics and anti-diarrheals. Pages 3-71 describe a male patient treated for life-threatening DKA and Pyelonephritis who took discharge on request. **Action Required:** Verify patient identity and discard Pages 1-2 from this medical record.
* **Unsafe Discharge Plan:** Patient was treated for DKA and Pyelonephritis but is being discharged with only Orthopedic painkillers (Ultracet, Etoshine). No insulin, oral hypoglycemics, or antibiotics are documented for discharge.

### ⚠️ Medication Reconciliation Concerns
* **Undocumented Stop:** Patient's home "Ayurvedic medication" for T2DM was stopped upon admission. [MISSING - CLINICIAN REVIEW REQUIRED: No clinical reason explicitly documented, though implied by DKA].
* **Missing Discharge Meds:** IV Meropenem and Insulin infusions were administered during the hospital stay, but no oral step-down therapy is documented for discharge.

### ❓ Missing Information
* Patient Name
* Patient Age
* Follow-up Instructions

### ⏳ Pending Results
* Blood Culture
* X-ray Pelvis
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)
