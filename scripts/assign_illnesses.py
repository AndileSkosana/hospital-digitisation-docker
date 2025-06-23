import pandas as pd
import numpy as np
import json
import random
import logging
import os
import sys
from datetime import datetime

# Import shared utility functions and configuration
from utils import get_age_group, calculate_age
from simulation_config import PEOPLE_DATA_FILE, ILLNESSES_FILE

# --- Configuration & Data Structures ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# --- Define possible conditions for special cases ---
CHRONIC_CONDITIONS = ["Diabetes", "Hypertension", "Asthma", "Arthritis", "Heart Disease", "Chronic Kidney Disease"]
PALLIATIVE_CONDITIONS = ["Advanced Cancer", "End-Stage Organ Failure", "Severe Neurological Disease"]
TRANSPLANT_TYPES = ["Kidney Transplant", "Heart Transplant", "Liver Transplant", "Lung Transplant"]
NO_ILLNESS_REPORTED = "No significant illness reported"

# --- Define the age-specific illness probabilities and remedies ---
AGE_SPECIFIC_ISSUE_PROBS = {
    "Chest pain": {
        "45-64": {"probability": 0.02, "emt_remedies": ["Oxygen", "Aspirin"], "hospital_remedies": ["ECG", "Blood tests", "Oxygen", "Nitrates"]},
        "65+": {"probability": 0.05, "emt_remedies": ["Oxygen", "Aspirin"], "hospital_remedies": ["ECG", "Blood tests", "Oxygen", "Nitrates", "Aspirin"]},
        "default": {"probability": 0.005, "emt_remedies": ["Observation"], "hospital_remedies": ["ECG", "Observation"]}
    },
    "Burns": {
        "0-4": {"probability": 0.02, "emt_remedies": ["Cold water immersion"], "hospital_remedies": ["Burn dressings", "Pain management"]},
        "default": {"probability": 0.005, "emt_remedies": ["Assessment"], "hospital_remedies": ["Wound dressing"]}
    },
    "Stroke symptoms": {
        "65+": {"probability": 0.008, "emt_remedies": ["Neurological assessment"], "hospital_remedies": ["Imaging (CT/MRI)", "Antiplatelets"]},
        "default": {"probability": 0.001, "emt_remedies": ["Neurological assessment"], "hospital_remedies": ["Imaging (CT/MRI)"]}
    },
    "Common Cold/Flu": {
        "default": {"probability": 0.20, "emt_remedies": ["Rest", "Fluids"], "hospital_remedies": ["Symptomatic relief", "Antipyretics"]}
    },
    "Chronic Condition": {
        "45-64": {"probability": 0.35, "emt_remedies": ["Assessment"], "hospital_remedies": ["Management plan", "Medication review"]},
        "65+": {"probability": 0.50, "emt_remedies": ["Assessment"], "hospital_remedies": ["Management plan", "Complication management"]},
        "default": {"probability": 0.10, "emt_remedies": ["Assessment"], "hospital_remedies": ["Condition-specific assessment"]}
    },
    "Palliative Care Need": {
        "65+": {"probability": 0.05, "emt_remedies": ["Pain management"], "hospital_remedies": ["Symptom control", "End-of-life care planning"]},
        "default": {"probability": 0.005, "emt_remedies": ["Assessment"], "hospital_remedies": ["Assessment for palliative needs"]}
    },
    "Transplant Assessment": {
        "25-44": {"probability": 0.01, "emt_remedies": ["Assessment"], "hospital_remedies": ["Organ function tests", "Eligibility assessment"]},
        "default": {"probability": 0.001, "emt_remedies": ["Assessment"], "hospital_remedies": ["Eligibility assessment"]}
    },
    "No significant illness reported": {
        "default": {"probability": 0.65, "emt_remedies": ["N/A"], "hospital_remedies": ["Routine check-up"]}
    }
}


def assign_illnesses_chunked(people_csv_filepath, output_csv_filepath, chunksize=10000):
    """
    Efficiently assigns illnesses and remedies in chunks to prevent memory issues.
    """
    logging.info(f"Starting illness assignment from '{people_csv_filepath}'")
    
    try:
        chunk_iterator = pd.read_csv(people_csv_filepath, chunksize=chunksize, iterator=True)
    except FileNotFoundError:
        logging.error(f"Input file not found: {people_csv_filepath}")
        return

    is_first_chunk = True
    for chunk in chunk_iterator:
        chunk['Age'] = chunk['Birthdate'].apply(calculate_age)
        chunk['age_group_at_assessment'] = chunk['Age'].apply(get_age_group)
        
        chunk_issues = [[] for _ in range(len(chunk))]
        chunk_emt = [[] for _ in range(len(chunk))]
        chunk_hospital = [[] for _ in range(len(chunk))]

        for i, person in chunk.iterrows():
            person_index_in_chunk = chunk.index.get_loc(i)
            for issue, age_group_info in AGE_SPECIFIC_ISSUE_PROBS.items():
                age_group = person["age_group_at_assessment"]
                age_data = age_group_info.get(age_group, age_group_info.get("default", {}))
                probability = age_data.get("probability", 0)

                if random.random() < probability:
                    if issue == "Chronic Condition":
                        chunk_issues[person_index_in_chunk].append(f"Chronic Condition: {random.choice(CHRONIC_CONDITIONS)}")
                    elif issue == "Palliative Care Need":
                        chunk_issues[person_index_in_chunk].append(f"Palliative Care Need: {random.choice(PALLIATIVE_CONDITIONS)}")
                    elif issue == "Transplant Assessment":
                        chunk_issues[person_index_in_chunk].append(f"Transplant Assessment: {random.choice(TRANSPLANT_TYPES)}")
                    else:
                        chunk_issues[person_index_in_chunk].append(issue)
                    
                    chunk_emt[person_index_in_chunk].extend(age_data.get("emt_remedies", []))
                    chunk_hospital[person_index_in_chunk].extend(age_data.get("hospital_remedies", []))

        for i in range(len(chunk_issues)):
            if not chunk_issues[i]:
                chunk_issues[i] = [NO_ILLNESS_REPORTED]
                chunk_emt[i] = ["N/A"]
                chunk_hospital[i] = ["Routine check-up"]
        
        chunk['assigned_issues'] = chunk_issues
        chunk['emt_remedies'] = chunk_emt
        chunk['hospital_remedies'] = chunk_hospital

        # Convert list columns to JSON strings for CSV compatibility
        for col in ['assigned_issues', 'emt_remedies', 'hospital_remedies']:
            chunk[col] = chunk[col].apply(json.dumps)

        if is_first_chunk:
            chunk.to_csv(output_csv_filepath, mode='w', header=True, index=False)
            is_first_chunk = False
        else:
            chunk.to_csv(output_csv_filepath, mode='a', header=False, index=False)
            
        logging.info(f"Processed and saved a chunk of {len(chunk)} records.")

    logging.info(f"Finished assigning illnesses. Final data saved to '{output_csv_filepath}'")


if __name__ == "__main__":
    assign_illnesses_chunked(PEOPLE_DATA_FILE, ILLNESSES_FILE)
