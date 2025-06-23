import pandas as pd
import random
import logging
import os
import sys
from datetime import datetime
from simulation_config import ILLNESSES_FILE, BATCH_DATA_PATH

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def generate_admissions(sim_date_str, num_admissions=150):
    """Generates a batch file for daily patient admissions."""
    output_path = f"{BATCH_DATA_PATH}/admissions_{sim_date_str}.csv"
    try:
        people_df = pd.read_csv(ILLNESSES_FILE)
    except FileNotFoundError:
        logging.error(f"{ILLNESSES_FILE} not found. Cannot generate admissions.")
        return

    admissions = []
    # Ensure we don't try to sample more people than exist
    sample_size = min(num_admissions, len(people_df))
    patients_today = people_df.sample(n=sample_size)
    
    for _, person in patients_today.iterrows():
        admissions.append({
            'person_id': person['person_id'],
            'admission_date': f"{sim_date_str} {random.randint(0,23):02d}:{random.randint(0,59):02d}",
            'condition': person['Condition'],
            'emt_remedies': person['emt_remedies'],
            'hospital_remedies': person['hospital_remedies']
        })
    
    pd.DataFrame(admissions).to_csv(output_path, index=False)
    logging.info(f"Generated admissions file: {output_path}")

if __name__ == "__main__":
     if len(sys.argv) > 1:
        generate_admissions(sys.argv[1])
     else:
        logging.error("No simulation date provided to generate_patient_admissions.py.")
