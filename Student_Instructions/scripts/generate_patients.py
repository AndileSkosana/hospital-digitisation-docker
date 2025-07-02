import pandas as pd
import random
import os
import logging
import ast
from datetime import datetime, timedelta
import sys

# Import shared configuration and utilities
from simulation_config import (
    REDUCED_PATIENT_PERIOD_START, NORMAL_PATIENT_PERIOD_RESUME,
    MONTHLY_PATIENT_LIMIT, REDUCED_PATIENT_LIMIT,
    ILLNESSES_FILE, BATCH_DATA_PATH
)
# Import constants from utils
from utils import (
    calculate_age,
    FLU_PEAK_MONTHS, ACCIDENT_PEAK_MONTHS, BURN_PEAK_MONTHS, ASSAULT_PEAK_MONTHS,
    ALCOHOL_PEAK_MONTHS, POISONING_PEAK_MONTHS, MALNUTRITION_PEAK_MONTHS,
    OUTPATIENT_CONDITIONS, INPATIENT_DEPARTMENT_MAP
)

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# Constants for this script
HOURLY_ARRIVAL_WEIGHTS = [1]*7 + [3]*10 + [1]*7

def load_people_data(filename):
    """Loads and parses the population data."""
    try:
        people_df = pd.read_csv(filename)
        for col in ['assigned_issues', 'emt_remedies', 'hospital_remedies']:
            if col in people_df.columns:
                people_df[col] = people_df[col].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else [])
        return people_df
    except FileNotFoundError:
        logging.error(f"Error: File not found: {filename}")
        return None

def generate_daily_visitors(people_df, sim_date):
    """Generates a list of all patient visits for a single simulated day, including seasonal peaks."""
    patient_visit_data = []
    month = sim_date.month
    
    # Determine daily patient intake
    patient_limit = REDUCED_PATIENT_LIMIT if REDUCED_PATIENT_PERIOD_START.date() <= sim_date.date() < NORMAL_PATIENT_PERIOD_RESUME.date() else MONTHLY_PATIENT_LIMIT
    base_intake = random.randint(300, int(patient_limit / 30))
    
    seasonal_cases = []
    # Specific seasonal cases based on the month
    if month in FLU_PEAK_MONTHS:
        seasonal_cases.extend([{"condition": "Flu Symptoms", "Patient_Type": "Outpatient"}] * int(base_intake * 0.15))
    if month in ACCIDENT_PEAK_MONTHS:
        seasonal_cases.extend([{"condition": "Trauma", "Patient_Type": "Inpatient"}] * int(base_intake * 0.10))
    if month in BURN_PEAK_MONTHS:
        seasonal_cases.extend([{"condition": "Burns", "Patient_Type": "Inpatient"}] * int(base_intake * 0.05))
    if month in ASSAULT_PEAK_MONTHS:
        seasonal_cases.extend([{"condition": "Assault-related injuries", "Patient_Type": "Inpatient"}] * int(base_intake * 0.05))
    if month in ALCOHOL_PEAK_MONTHS:
         seasonal_cases.extend([{"condition": "Alcohol-related illness", "Patient_Type": "Inpatient"}] * int(base_intake * 0.05))
    if month in POISONING_PEAK_MONTHS:
         seasonal_cases.extend([{"condition": "Poisoning", "Patient_Type": "Inpatient"}] * int(base_intake * 0.02))
    if month in MALNUTRITION_PEAK_MONTHS:
         seasonal_cases.extend([{"condition": "Malnutrition", "Patient_Type": "Inpatient"}] * int(base_intake * 0.02))

    sampled_people = people_df.sample(n=base_intake, replace=True)

    for i, person_row in enumerate(sampled_people.iterrows()):
        _, person_data = person_row
        
        if i < len(seasonal_cases):
            condition = seasonal_cases[i]["condition"]
        else:
            assigned_issues = person_data.get('assigned_issues', [])
            condition = random.choice(assigned_issues) if assigned_issues else "No significant illness reported"
        
        base_condition = condition.split(":")[0].strip()
        patient_type = "Outpatient" if base_condition in OUTPATIENT_CONDITIONS else "Inpatient"
        department = INPATIENT_DEPARTMENT_MAP.get(base_condition, "General Medicine")
        
        arrival_hour = random.choices(range(24), weights=HOURLY_ARRIVAL_WEIGHTS, k=1)[0]
        arrival_time = sim_date.replace(hour=arrival_hour, minute=random.randint(0, 59))
        
        patient_visit_data.append({
            "person_id": person_data["person_id"],
            "First_Name": person_data["First_Name"], "Surname": person_data["Surname"],
            "Age": person_data.get("Age", calculate_age(person_data["Birthdate"])),
            "condition": condition,
            "arrival_time": arrival_time.strftime("%Y-%m-%d %H:%M"),
            "Patient_Type": patient_type,
            "Department": department
        })

    return patient_visit_data

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_patients.py <YYYY-MM-DD>")
        sys.exit(1)
        
    sim_date_str = sys.argv[1]
    sim_date = datetime.strptime(sim_date_str, "%Y-%m-%d")
    
    people_data = load_people_data(ILLNESSES_FILE)
    if people_data is not None:
        daily_visitors = generate_daily_visitors(people_data, sim_date)
        
        output_file = f"{BATCH_DATA_PATH}/daily_visitors_{sim_date_str}.csv"
        pd.DataFrame(daily_visitors).to_csv(output_file, index=False)
        
        logging.info(f"Generated {len(daily_visitors)} total patient visits for {sim_date_str} and saved to {output_file}")
