import pandas as pd
import random
import os
import logging
from datetime import datetime, timedelta
import json
import sys
import numpy as np

# Import shared configuration
from simulation_config import PROCESSED_DATA_PATH, BATCH_DATA_PATH
from kafka import KafkaProducer, errors

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# Data & Logic Constants
REASONS = [
    "Emergency Transfer", "ICU Admission", "Specialist Consultation", "Step-down Facility",
    "Mental Health Evaluation", "Pediatric Transfer", "Maternal Complications", "Dialysis Requirement",
    "Rehabilitation Services", "Diagnostic Imaging", "Transfer for Surgery"
]
TRANSPORT_MODES = ["Ambulance", "Private Vehicle", "Medical Taxi", "Hospital Shuttle"]

CLINICS_DATA = {
    "Alexandra CHC": {"Location": "Wynberg", "Services Provided": ["Primary Healthcare", "HIV/AIDS Treatment & Counseling", "TB Screening & Treatment", "Maternity Services"]},
    "Chiawelo CHC": {"Location": "Diepkloof", "Services Provided": ["General Consultations", "Maternal & Child Health", "Mental Health Services", "Emergency & Trauma Unit"]},
    "Itereleng CHC": {"Location": "Dobsonville", "Services Provided": ["General Primary Healthcare", "Immunizations & Pediatric Care", "Physiotherapy & Rehabilitation"]},
    "Jabulani/Zola CHC": {"Location": "Soweto", "Services Provided": ["Emergency Care", "Maternal & Child Health Services", "Community Outreach Programs"]},
    "Lilian Ngoyi CHC": {"Location": "Diepkloof", "Services Provided": ["Maternity Services", "Palliative Care", "Dental & Eye Care", "Reproductive Health"]}
}
HOSPITALS_DATA = {
    "Charlotte Maxeke Hospital": {"Location": "Johannesburg", "Services Provided": ["Specialist Referrals", "Surgical Procedures", "Cardiology & Stroke Care", "Oncology & Chemotherapy", "Organ Transplants"]},
    "Helen Joseph Hospital": {"Location": "Auckland Park", "Services Provided": ["General Medicine", "General Surgery", "Orthopedics", "Pediatrics", "Obstetrics and Gynecology"]},
    "Rahima Moosa Hospital": {"Location": "Johannesburg", "Services Provided": ["Obstetrics & Gynecology", "Prenatal & Postnatal Care", "General Surgery", "Mental Health Services"]},
    "Leratong Hospital": {"Location": "Krugersdorp", "Services Provided": ["Emergency Services", "Internal Medicine", "General Surgery", "Pediatrics", "Orthopedics"]}
}

def get_kafka_producer(kafka_config):
    """Initializes and returns a KafkaProducer instance."""
    try:
        return KafkaProducer(
            bootstrap_servers=kafka_config['bootstrap_servers'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    except errors.NoBrokersAvailable:
        logging.error("Kafka brokers not available.")
        return None

def determine_transfer_destination(reason):
    """Decides the best facility based on the transfer reason."""
    if reason in ["Emergency Transfer", "ICU Admission", "Dialysis Requirement", "Transfer for Surgery", "Specialist Consultation"]:
        return random.choice(list(HOSPITALS_DATA.keys()))
    elif reason in ["Step-down Facility", "Rehabilitation Services", "Follow-up Care"]:
        step_down_facilities = [name for name, data in CLINICS_DATA.items() if "Rehabilitation" in data.get("Services Provided", [])]
        return random.choice(step_down_facilities if step_down_facilities else list(CLINICS_DATA.keys()))
    else:
        return random.choice(list(CLINICS_DATA.keys()) + list(HOSPITALS_DATA.keys()))

def generate_patient_transfers(sim_date_str, session_num_str, total_sessions_str):
    """
    Generates realistic patient transfer events based on the previous day's admissions,
    then sends them to Kafka.
    """
    session_num = int(session_num_str)
    total_sessions = int(total_sessions_str)

    admissions_file = f"{PROCESSED_DATA_PATH}/admissions_{sim_date_str}.csv"
    
    try:
        admissions_df = pd.read_csv(admissions_file)
    except FileNotFoundError:
        logging.warning(f"Admissions file for {sim_date_str} not found in processed directory. No transfers to generate for this session.")
        return

    transfer_candidates = admissions_df[admissions_df['Patient_Type'] == 'Inpatient'].copy()
    if transfer_candidates.empty:
        logging.info(f"No eligible inpatient transfer candidates from admissions on {sim_date_str}.")
        return

    # Process only a chunk of transfer candidates for the current session
    if len(transfer_candidates) < total_sessions:
        session_candidates_df = transfer_candidates[transfer_candidates.index % total_sessions == session_num]
    else:
        candidate_chunks = np.array_split(transfer_candidates, total_sessions)
        session_candidates_df = candidate_chunks[session_num]
    
    if session_candidates_df.empty:
        logging.info(f"No transfer candidates to process for session {session_num + 1}/{total_sessions}.")
        return

    transfer_records = []
    for _, patient in session_candidates_df.iterrows():
        transfer_reason = random.choice(REASONS)
        source_location = patient["Department"]
        destination = determine_transfer_destination(transfer_reason)

        transfer_records.append({
            "person_id": patient["person_id"],
            "First_Name": patient.get("First_Name", "N/A"), "Surname": patient.get("Surname", "N/A"),
            "Age": patient.get("Age", "N/A"), "Condition": patient["condition"],
            "Transfer_Reason": transfer_reason,
            "Transfer_Date": (datetime.strptime(patient["admission_date"], "%Y-%m-%d %H:%M") + timedelta(hours=random.randint(4, 20))).strftime("%Y-%m-%d %H:%M"),
            "Transfer_From": source_location,
            "Transfer_To": destination,
            "Transport_Mode": random.choice(TRANSPORT_MODES)
        })

    # Send records to Kafka
    if transfer_records:
        with open('/app/configs/kafka_config.json', 'r') as f:
            kafka_config = json.load(f)
        producer = get_kafka_producer(kafka_config)
        
        if producer:
            topic = kafka_config['topics']['transfers']
            for record in transfer_records:
                producer.send(topic, record)
            producer.flush()
            producer.close()
            logging.info(f"Sent {len(transfer_records)} patient transfer events to Kafka.")

        # Save consolidated CSV to the BATCH directory
        transfer_df = pd.DataFrame(transfer_records)
        output_path = f"{BATCH_DATA_PATH}/hospital_transfers_{sim_date_str}_session_{session_num+1}.csv"
        transfer_df.to_csv(output_path, index=False)
        logging.info(f"Session {session_num+1}: Saved {len(transfer_records)} transfer events to {output_path}")

        # Save summary report to the BATCH directory
        summary_path = f"{BATCH_DATA_PATH}/patient_transfers_summary_{sim_date_str}_session_{session_num+1}.txt"
        with open(summary_path, 'w') as f:
            f.write(f"--- Transfers Report for Day Following: {sim_date_str}, Session {session_num+1} ---\n")
            f.write(f"Loaded {len(admissions_df)} admissions from the previous day.\n")
            f.write(f"Identified {len(transfer_candidates)} inpatient candidates for transfer.\n")
            f.write(f"Created {len(transfer_records)} transfer events.\n")
            f.write(f"Saved: {os.path.basename(output_path)}\n")
        logging.info(f"Saved transfer summary to {summary_path}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        logging.error("Usage: python generate_patient_transfers.py <YYYY-MM-DD> <session_num> <total_sessions>")
        sys.exit(1)
        
    generate_patient_transfers(sys.argv[1], sys.argv[2], sys.argv[3])
