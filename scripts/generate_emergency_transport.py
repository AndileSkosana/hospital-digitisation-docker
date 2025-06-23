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
        producer = KafkaProducer(
            bootstrap_servers=kafka_config['bootstrap_servers'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            client_id=kafka_config.get('client_id', 'emergency-transport-producer')
        )
        return producer
    except errors.NoBrokersAvailable:
        logging.error("Kafka brokers not available. Please ensure Kafka is running and accessible.")
        return None

def generate_transport(sim_date_str):
    """Generates a single emergency transport event and sends it to Kafka."""
    with open('/app/configs/kafka_config.json', 'r') as f:
        kafka_config = json.load(f)
    
    producer = get_kafka_producer(kafka_config)
    if not producer:
        return
        
    topic = kafka_config['topics']['transport']
    
    try:
        admissions_file = f"/app/lake/batch/admissions_{sim_date_str}.csv"
        admissions_df = pd.read_csv(admissions_file)
        
        if not admissions_df.empty:
            # Select a random patient from the day's admissions for the event
            patient = admissions_df.sample(1).iloc[0].to_dict()
            record = {
                'person_id': patient['person_id'],
                'condition': patient['condition'],
                'transport_type': 'Ambulance',
                'timestamp': datetime.now().isoformat()
            }
            producer.send(topic, record)
            producer.flush()
            logging.info(f"Sent emergency transport stream for patient {patient['person_id']}")
            
    except FileNotFoundError:
        logging.warning(f"Admissions file for {sim_date_str} not found. No emergency transport generated.")
    except Exception as e:
        logging.error(f"Error in emergency transport generation: {e}")
    finally:
        if producer:
            producer.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_transport(sys.argv[1])
    else:
        logging.error("No simulation date provided to generate_emergency_transport.py.")
