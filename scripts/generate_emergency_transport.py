import pandas as pd
import os
import logging
from datetime import datetime
import json
import sys
import numpy as np

# Import shared configuration and utility mappings
from simulation_config import STREAM_DATA_PATH, PROCESSED_DATA_PATH, BATCH_DATA_PATH
from kafka import KafkaProducer, errors
from utils import DEPARTMENT_TO_ROLE_MAP


# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def get_kafka_producer(kafka_config):
    """Initializes and returns a KafkaProducer instance for streaming transport records."""
    try:
        return KafkaProducer(
            bootstrap_servers=kafka_config['bootstrap_servers'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    except errors.NoBrokersAvailable:
        logging.error("Kafka brokers not available.")
        return None

def load_staff_schedule(sim_date):
    """Loads the staff schedule for the given simulation date."""
    schedule_month_str = sim_date.strftime("%Y-%m")
    schedule_file = f"{PROCESSED_DATA_PATH}/schedules_{schedule_month_str}.csv"
    try:
        df = pd.read_csv(schedule_file)
        return df[df['date'] == sim_date.strftime('%Y-%m-%d')]
    except FileNotFoundError:
        logging.warning(f"Staff schedule file '{schedule_file}' not found. Staff assignment will be limited.")
        return pd.DataFrame()

def get_available_staff(staff_df, role, department=None, experience_level=None):
    """
    Selects a random available staff member based on role, department, and optionally experience level.
    Falls back to any available staff of that role if no match is found.
    """
    role_staff = staff_df[staff_df['Role'] == role]
    if role_staff.empty:
        return "No Staff Available"
        
    if department:
        dept_staff = role_staff[role_staff['Department'] == department]
        if not dept_staff.empty:
            if experience_level:
                exp_dept_staff = dept_staff[dept_staff['Experience_Level'] == experience_level]
                if not exp_dept_staff.empty:
                    selected = exp_dept_staff.sample(n=1).iloc[0]
                    return f"{selected['First_Name']} {selected['Surname']}"
            selected = dept_staff.sample(n=1).iloc[0]
            return f"{selected['First_Name']} {selected['Surname']}"
    
    selected = role_staff.sample(n=1).iloc[0]
    return f"{selected['First_Name']} {selected['Surname']}"

def generate_emergency_transport(sim_date_str, session_num_str, total_sessions_str):
    """
    Generates transport records for a given simulation date and session.
    Assigns staff based on severity, department, and availability.
    """
    session_num = int(session_num_str)
    total_sessions = int(total_sessions_str)
    
    visitors_file = f"{PROCESSED_DATA_PATH}/daily_visitors_{sim_date_str}.csv"
    sim_date = datetime.strptime(sim_date_str, "%Y-%m-%d")

    try:
        visitors_df = pd.read_csv(visitors_file)
        on_duty_staff = load_staff_schedule(sim_date)
    except FileNotFoundError as e:
        logging.warning(f"Required file not found: {e}. Skipping transport generation.")
        return

    # Split visitors into session chunks
    visitor_chunks = np.array_split(visitors_df, total_sessions)
    session_visitors_df = visitor_chunks[session_num]

    if session_visitors_df.empty:
        logging.info(f"No visitors to process for session {session_num + 1}/{total_sessions}.")
        return

    # Filter staff by role
    paramedics_df = on_duty_staff[on_duty_staff['Role'] == 'EMT']
    doctors_df = on_duty_staff[on_duty_staff['Role'] == 'Doctor']
    nurses_df = on_duty_staff[on_duty_staff['Role'] == 'Nurse']

    transport_records = []
    unmatched_specialist_requests = []  # Track departments where no specialist was available

    for _, patient in session_visitors_df.iterrows():
        base_condition = patient["condition"].split(":")[0].strip()
        severity = int(patient.get("Severity", 2))
        is_emergency_case = severity >= 4 or patient["Age"] >= 60 or patient["Age"] < 10
        department = patient.get("Department", "General Medicine")
        
        if is_emergency_case:
            # Assign ambulance transport and emergency staff
            transport_type = "Ambulance"
            attending_paramedic = get_available_staff(on_duty_staff, "EMT")
            attending_physician = get_available_staff(doctors_df, "Doctor", experience_level="Senior") if severity == 5 else get_available_staff(doctors_df, "Doctor")
            attending_nurse = get_available_staff(nurses_df, "Nurse")
            notes = f"Emergency transport for patient with severity {severity} condition: {patient['condition']}"
        else:
            # Assign private transport and outpatient staff
            transport_type = "Private"
            attending_paramedic = "N/A"
            
            # Attempt to assign a specialist based on department
            specialist_role = DEPARTMENT_TO_ROLE_MAP.get(department)
            attending_specialist = "No Staff Available"
            if specialist_role:
                attending_specialist = get_available_staff(on_duty_staff, specialist_role, department)
                if attending_specialist == "No Staff Available":
                    unmatched_specialist_requests.append(department)

            # Assign general physician and nurse
            attending_physician = get_available_staff(doctors_df, "Doctor", department)
            attending_nurse = get_available_staff(nurses_df, "Nurse", department)

            # Compose notes based on whether a specialist was found
            if attending_specialist != "No Staff Available":
                notes = f"Patient arrived via private transport for {patient['condition']} and was seen by specialist {attending_specialist} in {department}."
            else:
                notes = f"Patient arrived via private transport for {patient['condition']} and was seen by Dr. {attending_physician} and Nurse {attending_nurse} in {department}."

        # Append the transport record
        transport_records.append({
            "patient_id": patient["person_id"],
            "First_Name": patient["First_Name"],
            "Surname": patient["Surname"],
            "Age": patient["Age"],
            "Condition": patient["condition"],
            "Severity": severity,
            "Transport_Date": patient["arrival_time"],
            "Transport_Type": transport_type,
            "Department": department,
            "Attending_Paramedic": attending_paramedic,
            "Attending_Physician": attending_physician,
            "Attending_Nurse": attending_nurse,
            "Notes": notes
        })

    # Stream records to Kafka and save to disk
    if transport_records:
        with open('/app/configs/kafka_config.json', 'r') as f:
            kafka_config = json.load(f)
        producer = get_kafka_producer(kafka_config)
        
        if producer:
            topic = kafka_config['topics']['transport']
            for record in transport_records:
                producer.send(topic, record)
            producer.flush()
            producer.close()

        # Save transport records to CSV
        transport_df = pd.DataFrame(transport_records)
        output_path = f"{BATCH_DATA_PATH}/hospital_emergency_transport_{sim_date_str}_session_{session_num+1}.csv"
        transport_df.to_csv(output_path, index=False)
        logging.info(f"Session {session_num+1}: Saved {len(transport_records)} transport events to {output_path}")

        # Generate summary report
        summary_path = f"{BATCH_DATA_PATH}/emergency_transport_summary_{sim_date_str}_session_{session_num+1}.txt"
        with open(summary_path, 'w') as f:
            f.write(f"Date Processed: {sim_date_str}\n")
            f.write(f"Session: {session_num + 1}/{total_sessions}\n")
            f.write(f"Total Visitors in Session: {len(session_visitors_df)}\n")
            f.write(f"Total Transport Records Created: {len(transport_records)}\n")
            f.write(f"Saved: {os.path.basename(output_path)}\n\n")
            
            f.write("--- Summary of Transport Cases ---\n")
            if not transport_df.empty:
                f.write("\nTransport_Types:\n")
                f.write(transport_df['Transport_Type'].value_counts().to_string())

                # Ambulance case breakdown
                ambulance_cases_df = transport_df[transport_df['Transport_Type'] == 'Ambulance']
                if not ambulance_cases_df.empty:
                    f.write("\n\n--- Ambulance Case Details ---\n")
                    f.write("\nSeverity Breakdown:\n")
                    f.write(ambulance_cases_df['Severity'].value_counts().sort_index().to_string())
                    f.write("\n\nDepartment Destinations:\n")
                    f.write(ambulance_cases_df['Department'].value_counts().to_string())
                    f.write("\n\nConditions:\n")
                    f.write(ambulance_cases_df['Condition'].value_counts().to_string())
                    f.write("\n\nAttending Physicians:\n")
                    f.write(ambulance_cases_df['Attending_Physician'].value_counts().to_string())
                    f.write("\n\nAttending Nurses:\n")
                    f.write(ambulance_cases_df['Attending_Nurse'].value_counts().to_string())
                    f.write("\n\nAttending Paramedics:\n")
                    f.write(ambulance_cases_df['Attending_Paramedic'].value_counts().to_string())

                # Private case breakdown
                private_cases_df = transport_df[transport_df['Transport_Type'] == 'Private']
                if not private_cases_df.empty:
                    f.write("\n\n--- Private Transport Case Details ---\n")
                    f.write("\nDepartment Destinations:\n")
                    f.write(private_cases_df['Department'].value_counts().to_string())
                    f.write("\n\nAttending Physicians:\n")
                    f.write(private_cases_df['Attending_Physician'].value_counts().to_string())
                    f.write("\n\nAttending Nurses:\n")
                    f.write(private_cases_df['Attending_Nurse'].value_counts().to_string())

                # Unmatched specialist requests
                if unmatched_specialist_requests:
                    f.write("\n\n--- Unmatched Specialist Requests ---\n")
                    unmatched_counts = pd.Series(unmatched_specialist_requests).value_counts()
                    f.write(unmatched_counts.to_string())

        logging.info(f"Saved transport summary to {summary_path}")

# Entry point for command-line execution
if __name__ == "__main__":
    if len(sys.argv) != 4:
        logging.error("Usage: python generate_emergency_transport.py <YYYY-MM-DD> <session_num> <total_sessions>")
        sys.exit(1)
        
    generate_emergency_transport(sys.argv[1], sys.argv[2], sys.argv[3])