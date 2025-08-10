import os
import sys
import json
from typing import Tuple, Optional, List, Dict

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.PFT_interpreter import PFTInterpreter, Pattern, Severity

def parse_expert_impression(impression_text: str) -> Tuple[Optional[Pattern], Optional[Severity]]:
    text = impression_text.lower()
    
    expert_pattern = None
    if "mixed" in text:
        expert_pattern = Pattern.MIXED
    elif "obstructive" in text:
        expert_pattern = Pattern.OBSTRUCTIVE
    elif "restrictive" in text:
        expert_pattern = Pattern.RESTRICTIVE
    elif "normal" in text or "unremarkable" in text:
        expert_pattern = Pattern.NORMAL

    expert_severity = None
    if "moderately severe" in text:
        expert_severity = Severity.MODERATELY_SEVERE
    elif "very severe" in text:
        expert_severity = Severity.VERY_SEVERE
    elif "severe" in text:
        expert_severity = Severity.SEVERE
    elif "moderate" in text:
        expert_severity = Severity.MODERATE
    elif "mild" in text:
        expert_severity = Severity.MILD
    elif expert_pattern == Pattern.NORMAL:
        expert_severity = Severity.NORMAL
        
    return expert_pattern, expert_severity

def validate():
    dataset_file_path = os.path.join(os.path.dirname(__file__), '..', 'PFT-data', 'PFT_data.json')
    interpreter = PFTInterpreter()
    
    try:
        with open(dataset_file_path, 'r') as f:
            pft_data_list: List[Dict] = json.load(f)
    except FileNotFoundError:
        print(f"Error: Dataset file not found at '{dataset_file_path}'.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{dataset_file_path}'. Please check the file format.")
        return

    if not isinstance(pft_data_list, list):
        print(f"Error: The JSON file at '{dataset_file_path}' does not contain a list of records.")
        return

    total_records = len(pft_data_list)
    
    if total_records == 0:
        print(f"Warning: The dataset file '{dataset_file_path}' is empty.")
        return

    print(f"Starting validation on {total_records} PFT records from a single file...\n")

    pattern_correct = 0
    severity_correct = 0
    both_correct = 0
    mismatches = []

    for idx, pft_data in enumerate(pft_data_list):
        record_identifier = pft_data.get('file_name', f'Record #{idx+1}')
        try:
            system_result = interpreter.interpret_pft(pft_data)
            system_pattern = system_result.pattern
            system_severity = system_result.severity

            if 'impression' not in pft_data:
                continue
                
            expert_pattern, expert_severity = parse_expert_impression(pft_data['impression'])

            is_pattern_match = (system_pattern == expert_pattern)
            is_severity_match = (system_severity == expert_severity)

            if is_pattern_match:
                pattern_correct += 1
            if is_severity_match:
                severity_correct += 1
            
            if is_pattern_match and is_severity_match:
                both_correct += 1
            else:
                mismatches.append({
                    "record": record_identifier,
                    "system": f"Pattern: {system_pattern.value}, Severity: {system_severity.value}",
                    "expert": f"Pattern: {expert_pattern.value if expert_pattern else 'N/A'}, Severity: {expert_severity.value if expert_severity else 'N/A'}",
                    "expert_text": pft_data['impression']
                })

        except Exception as e:
            print(f"  - ERROR processing {record_identifier}: {e}")

    print("\n" + "="*50)
    print("      PFT SYSTEM VALIDATION REPORT")
    print("="*50)
    print(f"Total Records Processed: {total_records}")
    
    pattern_accuracy = (pattern_correct / total_records) * 100
    severity_accuracy = (severity_correct / total_records) * 100
    overall_accuracy = (both_correct / total_records) * 100

    print(f"\n--- ACCURACY METRICS ---")
    print(f"Pattern Identification Accuracy:  {pattern_accuracy:.2f}% ({pattern_correct}/{total_records})")
    print(f"Severity Classification Accuracy: {severity_accuracy:.2f}% ({severity_correct}/{total_records})")
    print(f"Overall Agreement (Pattern & Severity): {overall_accuracy:.2f}% ({both_correct}/{total_records})")
    
    print(f"\n--- MISMATCH ANALYSIS ---")
    print(f"Found {len(mismatches)} records with disagreements.")
    if mismatches:
        print("Top 5 Mismatches for Review:")
        for i, mismatch in enumerate(mismatches[:5]):
            print(f"\n{i+1}. Record: {mismatch['record']}")
            print(f"   - System: {mismatch['system']}")
            print(f"   - Expert: {mismatch['expert']}")
    print("="*50)

if __name__ == "__main__":
    validate()