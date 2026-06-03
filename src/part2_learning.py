import json
import os
import csv
import copy
import difflib
from src.state import AgentState
from src.agent import DischargeSummaryAgent
from src.logger import TraceLogger

class CorrectionMemory:
    def __init__(self):
        self.memory = {}

    def add_correction(self, field: str, value: str):
        if field == "medications.discharge":
            if field not in self.memory:
                self.memory[field] = []
            if value not in self.memory[field]:
                self.memory[field].append(value)
        else:
            self.memory[field] = value

    def get_dict(self):
        return self.memory

class SimulatedReviewer:
    def review(self, state: AgentState):
        edited_state = copy.deepcopy(state)
        edits_made = []

        # Policy 1: Standard discharge meds for DKA
        has_dka = any("Diabetic Ketoacidosis" in d for d in edited_state.diagnoses.principal)
        if has_dka:
            new_med = "Insulin Glargine 10U SC OD"
            has_new_med = any(new_med in m for m in edited_state.medications.discharge)
            if not has_new_med:
                edited_state.medications.discharge.append(new_med)
                edits_made.append({
                    "field": "medications.discharge", 
                    "added": new_med, 
                    "reason": "Standard DKA discharge medication missing."
                })

        # Policy 2: Follow-up instructions
        if "MISSING" in edited_state.follow_up_instructions:
            suggestion = "Follow up with Endocrinology OPD in 1 week. Return to ER if fever or vomiting occurs."
            if suggestion not in edited_state.follow_up_instructions:
                # The reviewer would typically completely rewrite a missing field
                edited_state.follow_up_instructions = suggestion
                edits_made.append({
                    "field": "follow_up_instructions", 
                    "added": suggestion, 
                    "reason": "Standard follow-up for DKA missing."
                })

        return edited_state, edits_made

def state_to_dict(state: AgentState) -> dict:
    return state.model_dump(exclude={"iteration_count", "raw_text"})

def calculate_reward(draft_state: AgentState, edited_state: AgentState):
    draft_dict = state_to_dict(draft_state)
    edited_dict = state_to_dict(edited_state)

    draft_json = json.dumps(draft_dict, sort_keys=True, default=str)
    edited_json = json.dumps(edited_dict, sort_keys=True, default=str)

    # Normalized edit distance (higher is better, 1.0 = identical)
    edit_distance_reward = difflib.SequenceMatcher(None, draft_json, edited_json).ratio()

    # Section-level accuracy
    total_sections = len(draft_dict)
    matching_sections = 0
    for key in draft_dict:
        if json.dumps(draft_dict[key], sort_keys=True, default=str) == json.dumps(edited_dict[key], sort_keys=True, default=str):
            matching_sections += 1
            
    section_accuracy = matching_sections / total_sections if total_sections > 0 else 0.0

    return edit_distance_reward, section_accuracy

def run_learning_loop(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    memory = CorrectionMemory()
    reviewer = SimulatedReviewer()
    
    metrics = []
    all_edits = []

    print("Starting Part 2: Learning from Doctor Edits...")
    
    for iteration in range(1, 6):
        print(f"\n--- Iteration {iteration} ---")
        
        # 1. Agent generates draft (using memory)
        logger = TraceLogger(os.path.join(output_dir, f"trace_iter_{iteration}.log"))
        agent = DischargeSummaryAgent(logger)
        
        # We intercept before final markdown generation to apply memory and get reviewer edits
        agent.run_mock(output_dir, memory=memory.get_dict(), skip_file_generation=True)
        draft_state = copy.deepcopy(agent.state)
        
        # 2. Reviewer edits draft
        edited_state, edits = reviewer.review(draft_state)
        
        # 3. Calculate Reward
        edit_score, sec_acc = calculate_reward(draft_state, edited_state)
        metrics.append({
            "iteration": iteration,
            "edit_distance_score": round(edit_score, 4),
            "section_accuracy": round(sec_acc, 4),
            "num_edits": len(edits)
        })
        
        print(f"Edits required: {len(edits)}")
        print(f"Edit Distance Score: {edit_score:.4f} (1.0 = perfect)")
        print(f"Section Accuracy: {sec_acc:.4f} (1.0 = perfect)")
        
        all_edits.append({
            "iteration": iteration,
            "edits": edits
        })
        
        # 4. Learning: Update memory from edits
        for edit in edits:
            memory.add_correction(edit["field"], edit["added"])

    # Save Outputs
    print("\nSaving Part 2 Outputs...")
    
    with open(os.path.join(output_dir, "reviewer_edits.json"), "w") as f:
        json.dump(all_edits, f, indent=2)
        
    with open(os.path.join(output_dir, "correction_memory.json"), "w") as f:
        json.dump(memory.get_dict(), f, indent=2)
        
    with open(os.path.join(output_dir, "part2_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
        
    with open(os.path.join(output_dir, "improvement_curve.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["iteration", "edit_distance_score", "section_accuracy", "num_edits"])
        writer.writeheader()
        writer.writerows(metrics)
        
    write_part2_report(output_dir, metrics)
    print(f"Part 2 complete. Outputs saved in {output_dir}/")

def write_part2_report(output_dir: str, metrics: list):
    baseline = metrics[0]
    final = metrics[-1]
    
    report = f"""# Part 2: Learning from Doctor Edits Report

## Executive Summary
This report demonstrates the implementation of a simulated doctor feedback loop where an autonomous agent learns to preemptively correct its drafts based on previous revisions, reducing the burden on human clinicians.

## Evaluation Results
The system underwent 5 iterations of simulated drafting, review, and learning.

* **Baseline (Iteration 1):** 
  * Edits Required: {baseline['num_edits']}
  * Section Accuracy: {baseline['section_accuracy']:.2%}
  * Edit Distance Score: {baseline['edit_distance_score']:.4f} (1.0 is perfect)
  
* **Final (Iteration 5):**
  * Edits Required: {final['num_edits']}
  * Section Accuracy: {final['section_accuracy']:.2%}
  * Edit Distance Score: {final['edit_distance_score']:.4f} (1.0 is perfect)

## Mechanism Design

1. **Reward Signal**: 
   * **Edit Distance Score**: We used normalized sequence matching (`difflib`) on the JSON state representations. A score of 1.0 means no string differences (less editing = higher reward).
   * **Section-Level Accuracy**: Measures the percentage of top-level JSON fields in the agent's draft that perfectly match the reviewer's final version.

2. **Simulated Reviewer**: 
   * A deterministic Python class that applies a hidden policy to the drafts (e.g., ensuring DKA patients always have Insulin on discharge, providing standard follow-up instructions for missing data).

3. **Learning Mechanism**: 
   * A lightweight `CorrectionMemory` that extracts exact modifications from the reviewer and stores them keyed by field. 
   * On subsequent drafts, the agent queries this memory and safely injects the learned suggestions without overriding guardrails.

4. **Safety Guarantees**: 
   * When injecting a learned suggestion into a missing field, the agent appends it as `[MISSING - CLINICIAN REVIEW REQUIRED] - Learned Suggestion: ...`. This strictly adheres to the Part 1 safety requirement that missing data must remain flagged, while still proposing the correct answer to the clinician (which the Simulated Reviewer accepts, reducing edit distance).
"""
    with open(os.path.join(output_dir, "part2_report.md"), "w") as f:
        f.write(report)
