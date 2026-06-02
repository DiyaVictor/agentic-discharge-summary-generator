import os
import json
from typing import Any, Dict

class TraceLogger:
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
        # Clear existing log file on initialization
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            f.write("")

    def log_step(
        self, 
        iteration: int, 
        reasoning: str, 
        action: str, 
        inputs: Dict[str, Any], 
        result: str, 
        next_decision: str
    ) -> None:
        """Logs a single step of the agent loop in a readable format."""
        
        # Format inputs safely for logging
        try:
            inputs_str = json.dumps(inputs, ensure_ascii=False)
        except TypeError:
            inputs_str = str(inputs)

        log_entry = (
            f"[ITERATION {iteration}]\n"
            f"Reasoning: {reasoning}\n"
            f"Action: {action}\n"
            f"Inputs: {inputs_str}\n"
            f"Result: {result}\n"
            f"Next Decision: {next_decision}\n\n"
        )

        # Append to file
        with open(self.log_file_path, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # Also print to console for real-time observability
        print(log_entry.strip())
