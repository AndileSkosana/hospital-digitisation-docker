import pandas as pd
import random
import os
import logging
from datetime import datetime, timedelta
import sys

# Import shared configuration
from simulation_config import BATCH_DATA_PATH
from utils import calculate_age

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# --- Detailed Constants & Mappings from your provided script ---
NO_ILLNESS_REPORTED = "No significant illness reported"
TRIAGE_DURATION = {
    "Critical": {"mean": 10, "std": 5}, "Severe": {"mean": 20, "std": 10},
    "Moderate": {"mean": 30, "std": 15}, "Mild": {"mean": 45, "std": 20},
    "Non-Urgent": {"mean": 60, "std": 30}
}
BED_CAPACITY = {
    "Inpatient": {
        "Obstetrics & Gynecology": {"Normal": 141, "Wards": ["Maternity Ward", "Gynae Ward"]},
        "Pediatrics": {"Normal": 219, "Wards": ["Pediatric Ward A", "Pediatric Ward B", "Neonatal ICU"]},
        "Medicine": {"Normal": 265, "Wards": ["General Med A", "General Med B", "Infectious Diseases"]},
        "Surgery": {"Normal": 330, "Wards": ["Surgical Ward 1", "Surgical Ward 2"]},
        "Oncology": {"Normal": 20, "Wards": ["Oncology Ward"]}, "ICU": {"Normal": 53, "Wards": ["Adult ICU"]},
        "Psychiatry": {"Normal": 20, "Wards": ["Psychiatric Ward"]}, "High Care": {"Normal": 32, "Wards": ["High Care Unit"]},
        "Palliative": {"Normal": 10, "Wards": ["Palliative Care Unit"]}, "Cardiology": {"Normal": 50, "Wards": ["Cardiac Ward", "CCU"]},
        "Neurology": {"Normal": 40, "Wards": ["Neurology Ward", "Stroke Unit"]},
    },
    "Outpatient": {
        "General Consultation": 300, "Emergency Room": 150, "Specialist Clinic": 100
    }
}
SEVERITY_LEVELS = {
    "Hypertension": "Moderate", "Diabetes": "Moderate", "Flu Symptoms": "Mild", "Trauma": "Severe",
    "Chest pain": "Critical", "Stroke symptoms": "Critical", "Severe shortness of breath or difficulty breathing": "Severe",
    "Major trauma": "Critical", "Burns": "Severe", "Poisoning": "Critical",
    NO_ILLNESS_REPORTED: "Non-Urgent", "Common Cold/Flu": "Mild"
}
INPATIENT_DEPARTMENT_MAP = {
    "Chronic Condition": "Medicine", "Palliative Care Need": "Palliative", "Trauma": "Surgery",
    "Chest pain": "Cardiology", "Stroke symptoms": "Neurology", "Major trauma": "Surgery", "Burns": "Surgery"
}

def load_staff_schedule(sim_date):
    """Loads the schedule for the specific month."""
    # --- FIX: Dynamically construct the monthly schedule filename ---
    schedule_month_str = sim_date.strftime("%Y-%m")
    schedule_file = f"{BATCH_DATA_PATH}/schedules_{schedule_month_str}.csv"
    try:
        df = pd.read_csv(schedule_file)
        # Ensure the date column is in datetime format for proper filtering
        df['date'] = pd.to_datetime(df['date'])
        # Return only the schedule for the specific day
        return df[df['date'].dt.date == sim_date.date()]
    except FileNotFoundError:
        logging.warning(f"Staff schedule file '{schedule_file}' not found. Staff assignment will be limited.")
        return pd.DataFrame()

def get_available_staff(staff_df, role, department=None):
    """Selects a random available staff member."""
    filtered_staff = staff_df[staff_df['Role'] == role]
    if department:
        dept_specific = filtered_staff[filtered_staff.get('Department') == department]
        if not dept_specific.empty:
            return dept_specific.sample(n=1).iloc[0]
    if not filtered_staff.empty:
        return filtered_staff.sample(n=1).iloc[0]
    return None

def generate_admissions(daily_visitors_df, sim_date, staff_schedule_df):
    """
    Processes daily visitors to generate admission records with triage, bed assignment,
    and staff allocation.
    """
    admission_records = []
    daily_beds = {ptype: {dept: cap.get("Normal") if isinstance(cap, dict) else cap for dept, cap in depts.items()} for ptype, depts in BED_CAPACITY.items()}

    doctors_on_duty = staff_schedule_df[staff_schedule_df['Role'] == 'Doctor']
    nurses_on_duty = staff_schedule_df[staff_schedule_df['Role'] == 'Nurse']

    for _, visitor in daily_visitors_df.iterrows():
        base_condition = visitor['condition'].split(":")[0].strip()
        triage_level = SEVERITY_LEVELS.get(base_condition, "Mild")
        triage_params = TRIAGE_DURATION.get(triage_level, TRIAGE_DURATION["Non-Urgent"])
        triage_duration = max(5, int(random.gauss(triage_params['mean'], triage_params['std'])))
        admission_time = datetime.strptime(visitor['arrival_time'], "%Y-%m-%d %H:%M")
        
        patient_type = visitor['Patient_Type']
        department = visitor.get('Department', INPATIENT_DEPARTMENT_MAP.get(base_condition, 'General Medicine'))
        
        admission_status = "Admitted"
        if daily_beds.get(patient_type, {}).get(department, 0) > 0:
            daily_beds[patient_type][department] -= 1
        else:
            admission_status = "Denied - Capacity Full"

        admitting_doctor, admitting_nurse = "N/A", "N/A"
        if admission_status == "Admitted":
            doctor = get_available_staff(doctors_on_duty, "Doctor", department)
            nurse = get_available_staff(nurses_on_duty, "Nurse", department)
            if doctor is not None: admitting_doctor = f"{doctor.get('First_Name', '')} {doctor.get('Surname', '')}".strip()
            if nurse is not None: admitting_nurse = f"{nurse.get('First_Name', '')} {nurse.get('Surname', '')}".strip()

        admission_records.append({
            "person_id": visitor["person_id"],
            "admission_date": admission_time.strftime("%Y-%m-%d %H:%M"),
            "triage_level": triage_level,
            "triage_duration_minutes": triage_duration,
            "condition": visitor["condition"],
            "Department": department,
            "Patient_Type": patient_type,
            "Admission_Status": admission_status,
            "Admitting_Doctor": admitting_doctor,
            "Admitting_Nurse": admitting_nurse
        })
        
    return pd.DataFrame(admission_records)

def generate_summary(admissions_df, visitors_df, sim_date_str):
    """Generates a text summary of the day's admissions and workload."""
    num_visits = len(visitors_df)
    admitted_df = admissions_df[admissions_df['Admission_Status'] == 'Admitted']
    num_admissions = len(admitted_df)
    admission_rate = (num_admissions / num_visits * 100) if num_visits > 0 else 0
    
    summary_content = f"""
    Hospital Admissions Summary for: {sim_date_str}
    ============================================
    Total Patient Visits: {num_visits}
    Total Admissions: {num_admissions}
    Admission Rate: {admission_rate:.2f}%
    """
    if num_admissions > 0:
        summary_content += "\n\n--- Admissions by Department ---\n" + admitted_df['Department'].value_counts().to_string()
        
        # --- FIX: Added more detailed summary sections ---
        summary_content += "\n\n--- Doctor Workload (Admissions) ---\n" + admitted_df['Admitting_Doctor'].value_counts().to_string()
        summary_content += "\n\n--- Nurse Workload (Admissions) ---\n" + admitted_df['Admitting_Nurse'].value_counts().to_string()
        
        summary_content += "\n\n--- Conditions by Department ---"
        conditions_by_dept = admitted_df.groupby('Department')['condition'].value_counts().to_string()
        summary_content += "\n" + conditions_by_dept
    
    summary_file = f"{BATCH_DATA_PATH}/hospital_summary_{sim_date_str}.txt"
    with open(summary_file, 'w') as f: f.write(summary_content)
    logging.info(f"Generated hospital summary: {summary_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_patient_admissions.py <YYYY-MM-DD>")
        sys.exit(1)
        
    sim_date_str = sys.argv[1]
    sim_date = datetime.strptime(sim_date_str, "%Y-%m-%d")
    visitors_file = f"{BATCH_DATA_PATH}/daily_visitors_{sim_date_str}.csv"
    
    try:
        daily_visitors_df = pd.read_csv(visitors_file)
        staff_schedule_df = load_staff_schedule(sim_date)
        
        admissions_df = generate_admissions(daily_visitors_df, sim_date, staff_schedule_df)
        
        if not admissions_df.empty:
            output_file = f"{BATCH_DATA_PATH}/admissions_{sim_date_str}.csv"
            admissions_df.to_csv(output_file, index=False)
            logging.info(f"Generated {len(admissions_df)} admission records and saved to {output_file}")
            generate_summary(admissions_df, daily_visitors_df, sim_date_str)
        else:
            logging.info("No admission records were generated for this day.")

    except FileNotFoundError:
        logging.error(f"Daily visitors file not found: {visitors_file}. Please run generate_patients.py first.")
    except Exception as e:
        logging.error(f"An error occurred: {e}", exc_info=True)
