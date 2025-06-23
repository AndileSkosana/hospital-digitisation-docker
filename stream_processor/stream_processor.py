import json
from kafka import KafkaConsumer, errors
import logging
import os
import datetime
import sys
import time

# Import the correct path from the central simulation configuration
from simulation_config import STREAM_DATA_PATH

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] {%(levelname)s} %(message)s')
CONFIG_PATH = '/app/configs/kafka_config.json'

def get_kafka_consumer(topics, kafka_config):
    """Initializes and returns a KafkaConsumer instance subscribed to specified topics."""
    # This function will retry connection until it succeeds
    while True:
        try:
            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=kafka_config['bootstrap_servers'],
                auto_offset_reset='earliest', # Start reading at the earliest message
                group_id='hospital-stream-processor-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            logging.info(f"Kafka Consumer subscribed to topics: {topics}")
            return consumer
        except errors.NoBrokersAvailable as e:
            logging.warning(f"Kafka brokers not available: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logging.error(f"Failed to connect Kafka Consumer: {e}")
            return None

def process_stream():
    """
    Main function to consume messages from Kafka and save them to the data lake.
    """
    # Ensure the output directory exists
    os.makedirs(STREAM_DATA_PATH, exist_ok=True)
    
    # Load Kafka configuration to get topics
    try:
        with open(CONFIG_PATH, 'r') as f:
            kafka_config = json.load(f)
        
        # Subscribe to all topics defined for streaming
        stream_topics = [
            kafka_config['topics'].get('transport'),
            kafka_config['topics'].get('transfers')
        ]
        # Filter out any None values if a topic key is missing
        stream_topics = [topic for topic in stream_topics if topic]

        if not stream_topics:
            logging.error("No stream topics found in kafka_config.json. Exiting.")
            sys.exit(1)

    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        logging.error(f"Failed to load or parse Kafka config: {e}")
        sys.exit(1)

    consumer = get_kafka_consumer(stream_topics, kafka_config)
    if not consumer:
        logging.error("Could not create Kafka consumer. Exiting.")
        sys.exit(1)

    logging.info("Stream Processor started. Waiting for messages...")

    for message in consumer:
        record = message.value
        topic = message.topic
        logging.info(f"Received record from topic '{topic}': {record}")
        
        # Create a unique filename for each message
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
        record_id = record.get('person_id', 'unknown_id')
        file_name = f"{topic.replace('.', '_')}_{record_id}_{timestamp}.json"
        file_path = os.path.join(STREAM_DATA_PATH, file_name)
        
        try:
            with open(file_path, 'w') as f:
                json.dump(record, f, indent=2)
            logging.info(f"Saved stream record to {file_path}")
        except IOError as e:
            logging.error(f"Failed to write record to file {file_path}: {e}")

if __name__ == "__main__":
    process_stream()
