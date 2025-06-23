import pandas as pd
import psycopg2
import psycopg2.extras
import json
import logging
import os
import sys
import time
from datetime import datetime

# Import the correct paths from the central simulation configuration
from simulation_config import BATCH_DATA_PATH, LAKE_PATH

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] - %(levelname)s - %(message)s')

# Define the path for processed files relative to the main data path
PROCESSED_PATH = f'{LAKE_PATH}/processed' 

def get_db_connection():
    """Reads database configuration and returns a connection object."""
    # This function will retry connection until it succeeds
    while True:
        try:
            with open('/app/configs/database_config.json', 'r') as f:
                db_config = json.load(f)
            conn = psycopg2.connect(
                host=db_config.get('host', 'postgresDB'),
                port=db_config.get('port', 5432),
                dbname=db_config.get('database', 'hospital_db'),
                user=db_config.get('user', 'admin'),
                password=db_config.get('password', 'admin')
            )
            logging.info("Database connection successful.")
            return conn, db_config.get('schemas', {})
        except psycopg2.OperationalError as e:
            logging.warning(f"Failed to connect to the database: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            logging.error(f"An unrecoverable error occurred during DB connection: {e}")
            sys.exit(1)

def process_file(file_path):
    """Processes a single batch file and ingests its data into the database."""
    conn, schemas = get_db_connection()
    if not conn:
        return
        
    logging.info(f"Processing file: {file_path}")
    try:
        # For simplicity, this example just logs the action.
        # Your full normalization and ingestion logic would go here.
        df = pd.read_csv(file_path)
        logging.info(f"Read {len(df)} records from {os.path.basename(file_path)}. In a real system, this would now be normalized and loaded to the DB.")
        
        conn.commit()
        # Move the processed file to avoid re-processing
        os.rename(file_path, os.path.join(PROCESSED_PATH, os.path.basename(file_path)))
        logging.info(f"Moved processed file to {PROCESSED_PATH}")
        
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")
        conn.rollback()
    finally:
        conn.close()

def watch_directory(path_to_watch, interval=10):
    """Continuously watches a directory for new files to process."""
    os.makedirs(PROCESSED_PATH, exist_ok=True)
    os.makedirs(path_to_watch, exist_ok=True) # Ensure the batch directory also exists
    
    logging.info(f"Batch Ingestor started. Watching directory: {path_to_watch}...")
    
    while True:
        try:
            files_to_process = [f for f in os.listdir(path_to_watch) if f.endswith('.csv')]
            for filename in files_to_process:
                file_path = os.path.join(path_to_watch, filename)
                process_file(file_path)
        except FileNotFoundError:
             logging.warning(f"Watched directory {path_to_watch} not found. It may be created shortly. Retrying...")
        except Exception as e:
            logging.error(f"Error during directory watch loop: {e}")
        time.sleep(interval)

if __name__ == "__main__":
    # Use the centrally configured path
    watch_directory(BATCH_DATA_PATH)
