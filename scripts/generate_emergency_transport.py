import pandas as pd
import random
import os
import logging
from datetime import datetime
import json
import sys
import ast
from kafka import KafkaProducer, errors

from simulation_config import PROCESSED_DATA_PATH, STREAM_DATA_PATH, BATCH_DATA_PATH

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# --- Logic from Notebook: Conditions that warrant emergency transport ---
EMERGENCY_CONDITIONS = [
    "Trauma", "Chest pain", "Severe shortness of breath or difficulty breathing",
    "Stroke symptoms", "Heavy, uncontrollable bleeding", "Major trauma", "Burns",
    "Assault-related injuries", "Poisoning", "Seizures", "Loss of consciousness or fainting",
    "Severe allergic reactions (anaphylaxis)", "Sudden confusion or change in mental status"
]

def get_kafka_producer(kafka_config):
    """Initializes and returns a KafkaProducer instance."""
    try:
        return KafkaProducer(
            bootstrap_servers=kafka_config['bootstrap_servers'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    except Exception as e:
        logging.error(f"Failed to connect Kafka producer: {e}")
        return None

def generate_emergency_transport(sim_date_str):
    """
    Generates detailed emergency transport records for serious cases,
    assigns staff from the correct monthly schedule, and creates daily files.
    """
    visitors_file = f"{BATCH_DATA_PATH}/daily_visitors_{sim_date_str}.csv"
    
    # --- Dynamically construct the monthly schedule filename ---
    sim_date = datetime.strptime(sim_date_str, "%Y-%m-%d")
    schedule_month_str = sim_date.strftime("%Y-%m")
    schedule_file = f"{PROCESSED_DATA_PATH}/schedules_{schedule_month_str}.csv"

    try:
        visitors_df = pd.read_csv(visitors_file)
        staff_schedules_df = pd.read_csv(schedule_file)
        on_duty_staff = staff_schedules_df[staff_schedules_df['date'] == sim_date_str]
    except FileNotFoundError as e:
        logging.warning(f"Required file not found for {sim_date_str}: {e}. Skipping transport generation.")
        return

    emergency_cases = visitors_df[
        visitors_df['condition'].apply(lambda c: isinstance(c, str) and any(ec in c for ec in EMERGENCY_CONDITIONS))
    ].copy()
    
    if emergency_cases.empty:
        logging.info(f"No qualifying emergency transport cases for {sim_date_str}.")
        return
        
    available_paramedics = on_duty_staff[on_duty_staff['Role'] == 'Paramedic']
    available_doctors = on_duty_staff[on_duty_staff['Role'] == 'Doctor']
    available_nurses = on_duty_staff[on_duty_staff['Role'] == 'Nurse']

    transport_records = []
    for _, patient in emergency_cases.iterrows():
        paramedic = available_paramedics.sample(1).iloc[0] if not available_paramedics.empty else {}
        doctor = available_doctors.sample(1).iloc[0] if not available_doctors.empty else {}
        nurse = available_nurses.sample(1).iloc[0] if not available_nurses.empty else {}
        
        transport_records.append({
            "patient_id": patient["person_id"],
            "First_Name": patient["First_Name"], "Surname": patient["Surname"], "Age": patient["Age"],
            "Condition": patient["condition"], "Transport_Date": patient["arrival_time"],
            "Transport_Type": "Ambulance",
            "Attending_Paramedic": paramedic.get('staff_id', 'N/A'),
            "Attending_Physician": doctor.get('staff_id', 'N/A'),
            "Attending_Nurse": nurse.get('staff_id', 'N/A'),
            "Notes": f"Emergency transport for patient with presenting condition: {patient['condition']}"
        })

    # Send to Kafka and save daily files
    with open('/app/configs/kafka_config.json', 'r') as f:
        kafka_config = json.load(f)
    producer = get_kafka_producer(kafka_config)
    
    if producer:
        topic = kafka_config['topics']['transport']
        for record in transport_records:
            producer.send(topic, record)
        producer.flush()
        producer.close()

    transport_df = pd.DataFrame(transport_records)
    output_path = f"{STREAM_DATA_PATH}/hospital_emergency_transport_{sim_date_str}.csv"
    transport_df.to_csv(output_path, index=False)
    logging.info(f"Saved {len(transport_records)} emergency transport events to {output_path}")

    summary_path = f"{STREAM_DATA_PATH}/emergency_transport_summary_{sim_date_str}.txt"
    with open(summary_path, 'w') as f:
        f.write(f"Date Processed: {sim_date_str}\n")
        f.write(f"Total Daily Visitors: {len(visitors_df)}\n")
        f.write(f"Total Transport Cases Created: {len(transport_records)}\n")
        f.write(f"Saved: {os.path.basename(output_path)}\n")
    logging.info(f"Saved transport summary to {summary_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_emergency_transport(sys.argv[1])
    else:
        logging.error("No simulation date provided.")
