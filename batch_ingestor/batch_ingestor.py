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
PROCESSED_PATH = f'{LAKE_PATH}/processed' 

def get_db_connection():
    """Reads database configuration and retries connection until it succeeds."""
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

def ingest_file(file_path):
    """Processes a single admissions CSV file and ingests its data into the database."""
    conn, schemas = get_db_connection()
    if not conn:
        return
        
    logging.info(f"Processing admissions file: {file_path}")
    try:
        # Step 1: Ensure the database schema and tables exist
        with conn.cursor() as cursor, open('/app/db_schema.sql', 'r') as schema_file:
            cursor.execute(schema_file.read())
        
        # Step 2: Read the admissions data
        df = pd.read_csv(file_path)
        
        # Step 3: Insert the data (placeholder for full normalization)
        logging.info(f"Read {len(df)} records from {os.path.basename(file_path)}. In a real system, this would now be normalized and loaded to the DB.")
        
        conn.commit()
        
        # Step 4: Move the processed file to avoid re-processing
        os.makedirs(PROCESSED_PATH, exist_ok=True)
        # Construct the full destination path
        destination_path = os.path.join(PROCESSED_PATH, os.path.basename(file_path))
        os.rename(file_path, destination_path)
        logging.info(f"Moved processed file to {destination_path}")
        
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")
        conn.rollback()
    finally:
        conn.close()

def watch_directory(path_to_watch, interval=10):
    """Continuously watches a directory for new admissions files to process."""
    os.makedirs(path_to_watch, exist_ok=True)
    os.makedirs(PROCESSED_PATH, exist_ok=True)
    
    logging.info(f"Batch Ingestor started. Watching directory: '{path_to_watch}' for new admissions files...")
    
    while True:
        try:
            # --- Added more logging for debugging ---
            all_files = os.listdir(path_to_watch)
            if not all_files:
                logging.info("No files found in batch directory. Waiting...")
            else:
                logging.info(f"Found files: {all_files}")

            files_to_process = [f for f in all_files if f.startswith('admissions_') and f.endswith('.csv')]
            
            if files_to_process:
                logging.info(f"Found {len(files_to_process)} admissions file(s) to process: {files_to_process}")
                for filename in files_to_process:
                    file_path = os.path.join(path_to_watch, filename)
                    ingest_file(file_path)
            else:
                 logging.info("No new 'admissions_' files to process this cycle.")
                
        except FileNotFoundError:
             logging.warning(f"Watched directory {path_to_watch} not found. Retrying...")
        except Exception as e:
            logging.error(f"Error during directory watch loop: {e}")
            
        time.sleep(interval)

if __name__ == "__main__":
    # Use the centrally configured path for batch data
    watch_directory(BATCH_DATA_PATH)
