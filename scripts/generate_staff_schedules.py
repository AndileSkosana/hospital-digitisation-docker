import pandas as pd
import random
from datetime import datetime, timedelta
import json
import os
import logging

# Import shared configuration constants
from simulation_config import SIM_START_DATE, SIM_END_DATE, STAFF_DATA_FILE, BATCH_DATA_PATH
from utils import classify_experience

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# --- Logic and Data Structures ---
SPECIALTY_DEPARTMENTS = {
    "Oncology": {"Senior": "Oncology Only", "Mid-Level": ["Oncology", "ICU"], "Junior": "Flexible"},
    "Neurology": {"Senior": "Neurology Only", "Mid-Level": ["Neurology", "ICU"], "Junior": "Flexible"},
    "Cardiology": {"Senior": "Cardiology Only", "Mid-Level": ["Cardiology", "ICU"], "Junior": "Flexible"},
}
GENERAL_MEDICINE_DEPARTMENTS = [
    "Emergency", "ICU", "Orthopedics", "Pediatrics", "Dietetics", "Radiology", "Ophthalmology",
    "Renal", "Surgical", "Dermatology", "Psychology", "Dentistry", "Optometry",
    "Gastroenterology", "Frail Care", "Pharmacy", "Psychiatry", "Otorhinolaryngology"
]
ALLIED_HEALTH_ROLES = [
    "Pathologist", "Pharmacist", "Dental Assistant", "Physiotherapist", "Anesthesiologist",
    "Radiographer", "Occupational Therapist", "Speech Therapist", "EMT", "Respiratory Therapist",
    "Dietitian", "Exercise Physiologist", "Dental Hygienist", "Radiation Therapist", "Laboratory Technician"
]
MEDICAL_ROLES = ["Doctor", "Surgeon", "Nurse"] + ALLIED_HEALTH_ROLES

def generate_all_schedules(staff_df, shift_config):
    """
    Generates and saves a separate schedule CSV file for each month of the simulation,
    using the detailed rotation and senior coverage logic.
    """
    logging.info("Generating detailed monthly staff schedules for the entire simulation period...")
    
    medical_shift_cycle = shift_config.get('medical_shift_daily_cycle', [])
    if not medical_shift_cycle:
        logging.error("'medical_shift_daily_cycle' not found or is empty in shift config.")
        return

    cycle_length_days = len(medical_shift_cycle)
    
    # --- FIX: Use 'shift_type' which is the correct key from the config file ---
    shift_details_map = {shift['shift_type']: shift for shift in medical_shift_cycle}

    # Initialize a persistent rotation state for each medical staff member
    medical_staff_rotation_state = {
        row['person_id']: random.randint(0, cycle_length_days - 1)
        for _, row in staff_df[staff_df['Role'].isin(MEDICAL_ROLES)].iterrows()
    }
    
    current_date = SIM_START_DATE
    while current_date <= SIM_END_DATE:
        month_start = current_date.replace(day=1)
        next_month_start = (month_start + timedelta(days=32)).replace(day=1)
        month_end = next_month_start - timedelta(days=1)
        
        schedules_for_month = []
        date_iter = month_start
        
        while date_iter <= month_end and date_iter <= SIM_END_DATE:
            daily_assignments = []
            daily_staffing_check = {}

            for _, person in staff_df.iterrows():
                staff_id = person["person_id"]
                role = person["Role"]
                
                if role in MEDICAL_ROLES:
                    cycle_day_index = (medical_staff_rotation_state.get(staff_id, 0) + (date_iter - SIM_START_DATE).days) % cycle_length_days
                    shift_info = medical_shift_cycle[cycle_day_index]
                    
                    assignment = {
                        'staff_id': staff_id,
                        'First_Name': person["First_Name"], 'Surname': person["Surname"],
                        'Role': role, 'Experience_Level': person['Experience_Level'],
                        'Years_of_Service': person['Years_of_Service'],
                        'date': date_iter.strftime('%Y-%m-%d'),
                        'Department': person['Department'],
                        'shift_name': shift_info['shift_type'],
                        'is_work_day': shift_info['is_work_day']
                    }
                    daily_assignments.append(assignment)

                    if shift_info['is_work_day']:
                        dept = assignment['Department']
                        if dept not in daily_staffing_check:
                            daily_staffing_check[dept] = []
                        daily_staffing_check[dept].append(person.to_dict())

            # Senior Staff Coverage Logic
            working_staff_ids = {a['staff_id'] for a in daily_assignments if a['is_work_day']}
            all_seniors_working_today = staff_df[(staff_df['Experience_Level'] == 'Senior') & (staff_df['person_id'].isin(working_staff_ids))]
            
            for dept, assigned_staff_list in daily_staffing_check.items():
                has_senior = any(staff['Experience_Level'] == "Senior" for staff in assigned_staff_list)
                if not has_senior and not all_seniors_working_today.empty:
                    senior_to_reassign = all_seniors_working_today.sample(n=1).iloc[0]
                    for assignment in daily_assignments:
                        if assignment['staff_id'] == senior_to_reassign['person_id']:
                            logging.warning(f"Reassigning Senior {assignment['First_Name']} to cover {dept} on {date_iter.date()}")
                            assignment['Department'] = dept
                            break

            schedules_for_month.extend(daily_assignments)
            date_iter += timedelta(days=1)
        
        output_path = f"{BATCH_DATA_PATH}/schedules_{month_start.strftime('%Y-%m')}.csv"
        pd.DataFrame(schedules_for_month).to_csv(output_path, index=False)
        logging.info(f"Generated schedule file: {output_path}")
        
        current_date = next_month_start

if __name__ == "__main__":
    try:
        staff_df = pd.read_csv(STAFF_DATA_FILE)
        with open('/app/configs/hospital_shift_config.json', 'r') as f:
            shift_config = json.load(f)
        
        generate_all_schedules(staff_df, shift_config)
        
    except FileNotFoundError as e:
        logging.error(f"Required data file not found: {e}. Please ensure generate_staff.py has run.")
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
