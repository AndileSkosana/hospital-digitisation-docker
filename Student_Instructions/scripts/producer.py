import json
import pandas as pd
from kafka import KafkaProducer
import logging
import os
import sys

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] {%(levelname)s} %(message)s')

def get_kafka_producer(kafka_config):
    """Initializes and returns a KafkaProducer instance."""
    try:
        producer = KafkaProducer(
            bootstrap_servers=kafka_config['bootstrap_servers'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            client_id=kafka_config.get('client_id', 'default-producer')
        )
        logging.info("Kafka Producer connected successfully.")
        return producer
    except Exception as e:
        logging.error(f"Failed to connect Kafka Producer: {e}")
        return None

def stream_data(producer, topic, file_path):
    """
    Reads data from a CSV file and streams each row to a specified Kafka topic.
    """
    try:
        if not os.path.exists(file_path):
            logging.warning(f"File not found: {file_path}. Nothing to stream.")
            return

        df = pd.read_csv(file_path)
        if df.empty:
            logging.info(f"File {file_path} is empty. No data to stream.")
            return

        logging.info(f"Streaming {len(df)} records from {file_path} to topic '{topic}'...")
        for record in df.to_dict(orient='records'):
            producer.send(topic, record)
        
        producer.flush() # Ensure all messages are sent
        logging.info(f"Successfully streamed all records to topic '{topic}'.")

    except Exception as e:
        logging.error(f"Error while streaming data from {file_path}: {e}")

def main(topic_key, file_path):
    """
    Main function to initialize producer and start streaming.
    """
    try:
        with open('/app/configs/kafka_config.json', 'r') as f:
            kafka_config = json.load(f)
        topic_name = kafka_config['topics'].get(topic_key)
        if not topic_name:
            logging.error(f"Topic key '{topic_key}' not found in kafka_config.json")
            return
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logging.error(f"Failed to load or parse Kafka config: {e}")
        return

    producer = get_kafka_producer(kafka_config)
    if producer:
        stream_data(producer, topic_name, file_path)
        producer.close()
        logging.info("Producer has finished sending messages and closed.")

if __name__ == "__main__":
    # This script is designed to be called with arguments:
    # python producer.py <topic_key> <file_path>
    if len(sys.argv) != 3:
        logging.error("Usage: python producer.py <topic_key> <file_path>")
        sys.exit(1)
    
    topic_key_arg = sys.argv[1]
    file_path_arg = sys.argv[2]
    
    main(topic_key_arg, file_path_arg)