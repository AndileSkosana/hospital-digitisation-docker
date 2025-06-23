import pandas as pd
import random
from datetime import datetime
import json
import sys
import logging
from kafka import KafkaProducer, errors

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def get_kafka_producer(kafka_config):
    """Initializes and returns a KafkaProducer instance."""
    try:
        return KafkaProducer(
            bootstrap_servers=kafka_config['bootstrap_servers'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    except errors.NoBrokersAvailable:
        logging.error("Kafka brokers not available. Cannot create producer.")
        return None

def generate_transfers(sim_date_str):
    """Generates a single patient transfer event and sends it to Kafka."""
    with open('/app/configs/kafka_config.json', 'r') as f:
        kafka_config = json.load(f)
    
    producer = get_kafka_producer(kafka_config)
    if not producer:
        return
        
    topic = kafka_config['topics']['transfers']
    
    try:
        admissions_file = f"/app/lake/batch/admissions_{sim_date_str}.csv"
        admissions_df = pd.read_csv(admissions_file)
        
        if not admissions_df.empty:
            patient = admissions_df.sample(1).iloc[0].to_dict()
            record = {
                'person_id': patient['person_id'],
                'from_department': patient.get('Department', 'Emergency'),
                'to_department': random.choice(['ICU', 'Surgery', 'General Ward']),
                'timestamp': datetime.now().isoformat()
            }
            producer.send(topic, record)
            producer.flush()
            logging.info(f"Sent transfer stream for patient {patient['person_id']}")
    except FileNotFoundError:
        logging.warning(f"Admissions file for {sim_date_str} not found. No transfers generated.")
    except Exception as e:
        logging.error(f"Error in transfer generation: {e}")
    finally:
        if producer:
            producer.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_transfers(sys.argv[1])
    else:
        logging.error("No simulation date provided to generate_patient_transfers.py.")
