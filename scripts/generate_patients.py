import pandas as pd
import random
import os
import logging
import ast
from datetime import datetime, timedelta
import sys

# Import shared configuration
from simulation_config import (
    REDUCED_PATIENT_PERIOD_START, NORMAL_PATIENT_PERIOD_RESUME,
    MONTHLY_PATIENT_LIMIT, REDUCED_PATIENT_LIMIT, FLU_PEAK_MONTHS, ACCIDENT_PEAK_MONTHS,
    ILLNESSES_FILE, BATCH_DATA_PATH
)

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# --- Constants for this script ---
HOURLY_ARRIVAL_WEIGHTS = [1]*7 + [3]*10 + [1]*7 # Higher weight for outpatient hours (7am-4pm)
# Define conditions that are typically handled on an outpatient basis
OUTPATIENT_CONDITIONS = ['Routine Check-up', 'Minor Injury', 'General Consultation', 'Flu Symptoms', "No significant illness reported"]

def load_people_data(filename):
    """Loads and parses the population data."""
    try:
        people_df = pd.read_csv(filename)
        # Safely evaluate string representations of lists
        for col in ['assigned_issues', 'emt_remedies', 'hospital_remedies']:
            people_df[col] = people_df[col].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else [])
        return people_df
    except FileNotFoundError:
        logging.error(f"Error: File not found: {filename}")
        return None

def generate_daily_visitors(people_df, sim_date):
    """Generates a list of all patient visits for a single simulated day."""
    patient_visit_data = []
    month = sim_date.month
    
    # Determine daily patient intake based on seasonality and special periods
    base_intake = random.randint(300, 500)
    if month in FLU_PEAK_MONTHS: base_intake = int(base_intake * 1.4)
    if month in ACCIDENT_PEAK_MONTHS: base_intake = int(base_intake * 1.3)

    patient_limit = REDUCED_PATIENT_LIMIT if REDUCED_PATIENT_PERIOD_START.date() <= sim_date.date() < NORMAL_PATIENT_PERIOD_RESUME.date() else MONTHLY_PATIENT_LIMIT
    daily_patient_intake = int(min(base_intake, patient_limit / 30))

    if daily_patient_intake == 0: return []

    sampled_people = people_df.sample(n=daily_patient_intake, replace=True)

    for _, person in sampled_people.iterrows():
        assigned_issues = person.get('assigned_issues', [])
        condition = random.choice(assigned_issues) if assigned_issues else "No significant illness reported"
        base_condition = condition.split(":")[0].strip()
        
        arrival_hour = random.choices(range(24), weights=HOURLY_ARRIVAL_WEIGHTS, k=1)[0]
        arrival_time = sim_date.replace(hour=arrival_hour, minute=random.randint(0, 59))
        
        # --- FIX: Determine Patient_Type instead of Transport_Method ---
        patient_type = "Outpatient" if base_condition in OUTPATIENT_CONDITIONS else "Inpatient"

        patient_visit_data.append({
            "person_id": person["person_id"],
            "First_Name": person["First_Name"], "Surname": person["Surname"],
            "Age": person["Age"], "condition": condition,
            "arrival_time": arrival_time.strftime("%Y-%m-%d %H:%M"),
            "Patient_Type": patient_type
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
