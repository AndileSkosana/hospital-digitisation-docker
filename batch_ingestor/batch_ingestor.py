import pandas as pd
import psycopg2
import psycopg2.extras
import json
import logging
import os
import sys
import time
from datetime import datetime
import re

# Import the correct paths from the central simulation configuration
from simulation_config import (
    BATCH_DATA_PATH, STREAM_DATA_PATH, LAKE_PATH, 
    STAFF_GENERATED_FLAG, WORKFORCE_SIMULATED_FLAG, SCHEDULES_GENERATED_FLAG
)

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
        if 'Role' not in df.columns: df['Role'] = 'Reserve'
        if 'Department' not in df.columns: df['Department'] = 'Reserve'
        if 'Experience_Level' not in df.columns: df['Experience_Level'] = 'N/A'
        if 'Years_of_Service' not in df.columns: df['Years_of_Service'] = 0
        if 'person_id' not in df.columns and 'Staff_ID' in df.columns: df['person_id'] = df['Staff_ID']
        if 'Staff_ID' not in df.columns and 'person_id' in df.columns: df['Staff_ID'] = df['person_id']
        
        df['staff_id'] = df['Staff_ID']
        staff_records = df.to_dict(orient='records')
        
        upsert_query = f"""
            INSERT INTO {operations_schema}.Staff (staff_id, person_id, first_name, surname, role, department, experience_level, years_of_service)
            VALUES (%(staff_id)s, %(person_id)s, %(First_Name)s, %(Surname)s, %(Role)s, %(Department)s, %(Experience_Level)s, %(Years_of_Service)s)
            ON CONFLICT (staff_id) DO UPDATE SET
                role = EXCLUDED.role, department = EXCLUDED.department,
                experience_level = EXCLUDED.experience_level, years_of_service = EXCLUDED.years_of_service;
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

def process_file(file_path, file_type):
    """Routes a file to the correct ingestion function based on its type."""
    conn, schemas = get_db_connection()
    if not conn: return
    try:
        with conn.cursor() as cursor, open('/app/db_schema.sql', 'r') as schema_file:
            cursor.execute(schema_file.read())
        
        df = pd.read_csv(file_path)

        if file_type == 'staff':
            ingest_staff_data(conn, schemas, df)
        elif file_type == 'schedule':
            ingest_schedules_data(conn, schemas, df)
        # Add other file handlers here
            
        conn.commit()
        destination_path = os.path.join(PROCESSED_PATH, os.path.basename(file_path))
        os.rename(file_path, destination_path)
        logging.info(f"Moved processed file to {destination_path}")
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}", exc_info=True)
        conn.rollback()
    finally:
        if conn: conn.close()

def watch_for_daily_files(paths_to_watch, interval=10):
    """Continuously watches for new daily admissions and stream files."""
    logging.info(f"Now watching for daily files in: {paths_to_watch}...")
    while True:
        try:
            for path in paths_to_watch:
                daily_files = [os.path.join(path, f) for f in os.listdir(path) if f.startswith(('admissions_', 'daily_visitors_')) or f.endswith('.json')]
                for file_path in daily_files:
                    # In a real system, you would add full processing logic here
                    logging.info(f"Found daily file: {os.path.basename(file_path)}. Moving to processed for now.")
                    os.rename(file_path, os.path.join(PROCESSED_PATH, os.path.basename(file_path)))
        except Exception as e:
            logging.error(f"Error during daily file watch loop: {e}", exc_info=True)
        time.sleep(interval)

if __name__ == "__main__":
    os.makedirs(PROCESSED_PATH, exist_ok=True)
    
    # --- FIX: New, robust, flag-driven ingestion logic ---

    # Phase 1: Ingest initial staff files once the staff flag is present
    logging.info("Waiting for staff generation to complete...")
    while not os.path.exists(STAFF_GENERATED_FLAG):
        time.sleep(5)
    logging.info("Staff generation complete. Ingesting initial staff and reserve files...")
    for f in ['staff_data.csv', 'reserve_pool.csv']:
        file_path = os.path.join(BATCH_DATA_PATH, f)
        if os.path.exists(file_path):
            process_file(file_path, 'staff')

    # Phase 2: Ingest quarterly workforce snapshots once they are ready
    logging.info("Waiting for workforce simulation to complete...")
    while not os.path.exists(WORKFORCE_SIMULATED_FLAG):
        time.sleep(5)
    logging.info("Workforce simulation complete. Ingesting quarterly snapshots...")
    all_files = os.listdir(BATCH_DATA_PATH)
    staff_snapshot_files = sorted([f for f in all_files if f.startswith('staff_active_')])
    for f in staff_snapshot_files:
        process_file(os.path.join(BATCH_DATA_PATH, f), 'staff')

    # Phase 3: Ingest schedules only after all staff data is in the DB
    logging.info("Waiting for schedule generation to complete...")
    while not os.path.exists(SCHEDULES_GENERATED_FLAG):
        time.sleep(5)
    logging.info("Schedule generation complete. Ingesting schedule files...")
    all_files = os.listdir(BATCH_DATA_PATH) # Re-check directory
    schedule_files = sorted([f for f in all_files if f.startswith('schedules_')])
    for f in schedule_files:
        process_file(os.path.join(BATCH_DATA_PATH, f), 'schedule')
        
    logging.info("✅ All initial setup files have been ingested.")
    
    # Phase 4: Begin watching for daily files
    watch_for_daily_files([BATCH_DATA_PATH, STREAM_DATA_PATH])
