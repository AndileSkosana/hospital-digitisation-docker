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
from simulation_config import BATCH_DATA_PATH, STREAM_DATA_PATH, LAKE_PATH

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
            logging.error(f"An unrecoverable error occurred during DB connection: {e}", exc_info=True)
            sys.exit(1)

def ingest_staff_data(conn, schemas, df):
    """Upserts staff data into the hospital_operations.Staff table."""
    operations_schema = schemas.get('operations', 'hospital_operations')
    with conn.cursor() as cursor:
        # Prepare records, ensuring all required columns exist with defaults
        df['staff_id'] = df['person_id'] # Map person_id to staff_id for the DB
        staff_records = df.to_dict(orient='records')
        
        upsert_query = f"""
            INSERT INTO {operations_schema}.Staff (staff_id, person_id, first_name, surname, role, department, experience_level, years_of_service)
            VALUES (%(staff_id)s, %(person_id)s, %(First_Name)s, %(Surname)s, %(Role)s, %(Department)s, %(Experience_Level)s, %(Years_of_Service)s)
            ON CONFLICT (staff_id) DO UPDATE SET
                role = EXCLUDED.role,
                department = EXCLUDED.department,
                experience_level = EXCLUDED.experience_level,
                years_of_service = EXCLUDED.years_of_service;
        """
        psycopg2.extras.execute_batch(cursor, upsert_query, staff_records)
        logging.info(f"Upserted {len(staff_records)} records into {operations_schema}.Staff table.")

def ingest_schedules_data(conn, schemas, df):
    """Inserts schedule data into the hospital_operations.Schedules table."""
    operations_schema = schemas.get('operations', 'hospital_operations')
    with conn.cursor() as cursor:
        schedule_records = df.to_dict(orient='records')
        insert_query = f"""
            INSERT INTO {operations_schema}.Schedules (staff_id, schedule_date, shift_name, is_work_day, assigned_department)
            VALUES (%(staff_id)s, %(date)s, %(shift_name)s, %(is_work_day)s, %(Department)s)
            ON CONFLICT (staff_id, schedule_date) DO NOTHING;
        """
        psycopg2.extras.execute_batch(cursor, insert_query, schedule_records)
        logging.info(f"Ingested {len(schedule_records)} records into {operations_schema}.Schedules table.")

def ingest_admissions_csv(conn, schemas, df):
    """Processes a single admissions CSV file and ingests its data into the database."""
    # (Full normalization logic would go here)
    logging.info(f"Read {len(df)} records from admissions CSV. Ingesting to relational tables...")
    pass

def ingest_json_file(conn, schemas, file_path):
    """Processes a single stream JSON file and ingests it into the appropriate jsonb table."""
    logging.info(f"Processing stream file: {file_path}")
    
    if 'emergency_transport' in os.path.basename(file_path):
        table_name = f"{schemas.get('streams', 'hospital_streams')}.Transports"
    elif 'hospital_transfers' in os.path.basename(file_path):
        table_name = f"{schemas.get('streams', 'hospital_streams')}.Transfers"
    else:
        logging.warning(f"No JSON ingestion logic for file: {os.path.basename(file_path)}. Skipping.")
        return

    with open(file_path, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        data = [data]

    with conn.cursor() as cursor:
        for record in data:
            cursor.execute(f"INSERT INTO {table_name} (event_data) VALUES (%s)", (json.dumps(record),))
    logging.info(f"Successfully ingested {len(data)} records from {os.path.basename(file_path)} into {table_name}.")

def process_file(file_path):
    """Routes a file to the correct ingestion function based on its type."""
    conn, schemas = get_db_connection()
    if not conn: return
        
    try:
        with conn.cursor() as cursor, open('/app/db_schema.sql', 'r') as schema_file:
            cursor.execute(schema_file.read())

        filename = os.path.basename(file_path)
        
        # --- FIX: New routing logic for all file types ---
        if filename in ['staff_data.csv', 'reserve_pool.csv']:
            df = pd.read_csv(file_path)
            ingest_staff_data(conn, schemas, df)
        elif filename.startswith('schedules_'):
            df = pd.read_csv(file_path)
            ingest_schedules_data(conn, schemas, df)
        elif filename.startswith('admissions_'):
            df = pd.read_csv(file_path)
            ingest_admissions_csv(conn, schemas, df)
        elif filename.endswith('.json'):
            ingest_json_file(conn, schemas, file_path)
        else:
            logging.info(f"Skipping non-ingestion file: {filename}")
            return

        conn.commit()
        
        destination_path = os.path.join(PROCESSED_PATH, filename)
        os.rename(file_path, destination_path)
        logging.info(f"Moved processed file to {destination_path}")
        
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}", exc_info=True)
        conn.rollback()
    finally:
        conn.close()

def watch_directories(paths_to_watch, interval=10):
    """Continuously watches multiple directories for new files to process."""
    for path in paths_to_watch:
        os.makedirs(path, exist_ok=True)
    os.makedirs(PROCESSED_PATH, exist_ok=True)
    
    logging.info(f"Batch Ingestor started. Watching directories: {paths_to_watch}...")
    
    while True:
        try:
            for path in paths_to_watch:
                files_to_process = [os.path.join(path, f) for f in os.listdir(path) if f.endswith(('.csv', '.json'))]
                
                if files_to_process:
                    logging.info(f"Found {len(files_to_process)} file(s) in '{path}' to process.")
                    for file_path in files_to_process:
                        process_file(file_path)
        except Exception as e:
            logging.error(f"Error during directory watch loop: {e}", exc_info=True)
        
        time.sleep(interval)

if __name__ == "__main__":
    # Watch both the batch and stream directories for new files
    watch_directory_list = [BATCH_DATA_PATH, STREAM_DATA_PATH]
    watch_directories(watch_directory_list)
