import json
import os
from src.state import AgentState
from src.logger import TraceLogger
from src.tools import (
    mock_pdf_ingestion,
    mock_extract_demographics,
    mock_extract_clinical_course,
    mock_escalate_to_clinician,
    mock_medication_reconciliation,
    mock_check_missing_data,
    generate_markdown_draft
)

class DischargeSummaryAgent:
    def __init__(self, logger: TraceLogger):
        self.logger = logger
        self.state = AgentState()

    def run_mock(self, output_dir: str, memory: dict = None, skip_file_generation: bool = False):
        res_1 = mock_pdf_ingestion("patient_records.pdf", True)
        self.logger.log_step(
            iteration=1,
            reasoning="Initiating document ingestion and OCR for 71 pages.",
            action="execute_tool(pdf_ingestion)",
            inputs={"file_path": "patient_records.pdf", "use_vlm_for_handwriting": True},
            result=res_1,
            next_decision="Route to Demographics Extraction."
        )

        demo_data = mock_extract_demographics()
        for k, v in demo_data.items():
            setattr(self.state.patient_demographics, k, v)
        self.logger.log_step(
            iteration=2,
            reasoning="Extracting patient demographics, admission/discharge dates, and allergies.",
            action="execute_tool(extract_demographics)",
            inputs={"text": "<extracted_text>"},
            result="Name: NULL, Age: NULL, Gender: \"she\" (p.1), \"his\" (p.46). Weight: 71kg (p.16). Admission: 26/02/2026. Discharge: 02/03/2026. Allergies: Not known.",
            next_decision="Route to Conflict Detection due to Gender mismatch."
        )

        clinical_data = mock_extract_clinical_course()
        self.state.admission_date = clinical_data["admission_date"]
        self.state.discharge_date = clinical_data["discharge_date"]
        self.state.diagnoses.principal = clinical_data["diagnoses"]["principal"]
        self.state.diagnoses.secondary = clinical_data["diagnoses"]["secondary"]
        self.state.diagnoses.conflicts = clinical_data["diagnoses"]["conflicts"]
        self.state.diagnoses.sources = clinical_data["diagnoses"]["sources"]
        self.state.hospital_course = clinical_data["hospital_course"]
        self.state.procedures = clinical_data["procedures"]
        self.state.allergies = clinical_data["allergies"]
        self.state.discharge_condition.status = clinical_data["discharge_condition"]["status"]
        self.state.discharge_condition.vitals = clinical_data["discharge_condition"]["vitals"]
        self.state.discharge_condition.sources = clinical_data["discharge_condition"]["sources"]
        
        self.logger.log_step(
            iteration=3,
            reasoning="Extracting diagnoses and hospital course.",
            action="execute_tool(extract_clinical_course)",
            inputs={"text": "<extracted_text>"},
            result="Diagnoses found: Acute Gastroenteritis (p.1), UTI (p.1), DKA (p.3, 54), T2DM (p.46), Pyelonephritis (p.41).",
            next_decision="Route to Conflict Detection due to disjointed clinical pathways."
        )

        res_4 = mock_escalate_to_clinician("Massive record mix-up. Pages 1-2 contradict Pages 3-71 entirely. Suspect mixed patient files.")
        self.logger.log_step(
            iteration=4,
            reasoning="Evaluating conflicting diagnoses and demographics. Page 1-2 indicates a female with Gastroenteritis discharged hemodynamically stable. Pages 3-71 indicate a male with DKA and Pyelonephritis discharged on request.",
            action="execute_tool(escalate_to_clinician)",
            inputs={"reason": "Massive record mix-up. Pages 1-2 contradict Pages 3-71 entirely. Suspect mixed patient files."},
            result=res_4,
            next_decision="Proceed with extraction using Pages 3-71 as primary source of truth."
        )

        med_data = mock_medication_reconciliation()
        self.state.medications.admission = med_data["admission"]
        self.state.medications.discharge = med_data["discharge"]
        self.state.medications.reconciliation_flags = med_data["reconciliation_flags"]
        self.state.medications.sources = med_data["sources"]
        
        self.logger.log_step(
            iteration=5,
            reasoning="Extracting medications for reconciliation.",
            action="execute_tool(medication_reconciliation)",
            inputs={"admission_meds": ["Ayurvedic meds"], "hospital_meds": ["Actrapid", "Lantus", "Meromac", "Pantoprazole", "Emeset"], "discharge_meds": ["Ultracet", "Etoshine"]},
            result="3 flags generated: 1) Ayurvedic meds stopped without reason. 2) No discharge meds for DKA/Pyelonephritis. 3) Page 2 meds (Raciper, Oflox TZ) belong to conflicting record.",
            next_decision="Route to Missing Data Check."
        )

        missing_data = mock_check_missing_data()
        self.state.follow_up_instructions = missing_data["follow_up_instructions"]
        self.state.pending_results = missing_data["pending_results"]
        self.state.clinician_review_required.safety_concerns = missing_data["clinician_review_required"]["safety_concerns"]
        self.state.clinician_review_required.missing_information = missing_data["clinician_review_required"]["missing_information"]
        
        self.logger.log_step(
            iteration=6,
            reasoning="Checking for pending labs and missing required fields.",
            action="execute_tool(check_missing_data)",
            inputs={"state": "<current_agent_state>"},
            result="Missing: Name, Age, Follow-up instructions. Pending: Blood Culture (p.69), X-ray Pelvis (p.57).",
            next_decision="Route to Draft Generation."
        )

        # Apply Correction Memory (Part 2)
        if memory:
            if "follow_up_instructions" in memory and "MISSING" in self.state.follow_up_instructions:
                self.state.follow_up_instructions += f" - Learned Suggestion: {memory['follow_up_instructions']}"
            
            if "medications.discharge" in memory:
                for med in memory["medications.discharge"]:
                    if not any(med in m for m in self.state.medications.discharge):
                        self.state.medications.discharge.append(f"{med} (Learned Suggestion)")

        self.logger.log_step(
            iteration=7,
            reasoning="All facts extracted, validated, and flagged. Generating final markdown and JSON drafts.",
            action="execute_tool(generate_draft)",
            inputs={"state": "<current_agent_state>", "enforce_citations": True},
            result="Drafts generated successfully with [MISSING] and [CONFLICT DETECTED] placeholders injected.",
            next_decision="END."
        )

        if skip_file_generation:
            return

        md_path = os.path.join(output_dir, "discharge_summary.md")
        json_path = os.path.join(output_dir, "discharge_summary.json")
        
        generate_markdown_draft(self.state, md_path)
        
        with open(json_path, "w", encoding="utf-8") as f:
            state_dict = self.state.model_dump(exclude={"iteration_count", "raw_text"})
            
            # Reformat JSON to exactly match the requested output structure
            formatted_json = {
                "file": "discharge_summary.json",
                "patient_demographics": {
                    "name": state_dict["patient_demographics"]["name"],
                    "age": state_dict["patient_demographics"]["age"],
                    "gender": state_dict["patient_demographics"]["gender"],
                    "weight": state_dict["patient_demographics"]["weight"],
                    "sources": ["p. 1", "p. 16", "p. 42", "p. 43", "p. 44", "p. 45", "p. 46"]
                },
                "admission_date": state_dict["admission_date"],
                "discharge_date": state_dict["discharge_date"],
                "diagnoses": state_dict["diagnoses"],
                "hospital_course": state_dict["hospital_course"],
                "procedures": state_dict["procedures"],
                "medications": state_dict["medications"],
                "allergies": state_dict["allergies"],
                "follow_up_instructions": state_dict["follow_up_instructions"],
                "pending_results": state_dict["pending_results"],
                "discharge_condition": state_dict["discharge_condition"],
                "clinician_review_required": state_dict["clinician_review_required"]
            }
            
            json.dump(formatted_json, f, indent=2, ensure_ascii=False)
