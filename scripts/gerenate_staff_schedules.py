import pandas as pd
import random
from datetime import datetime, timedelta
import json
import os
import logging

# Import shared configuration constants
from simulation_config import SIM_START_DATE, SIM_END_DATE, STAFF_DATA_FILE, STAFF_SCHEDULES_FILE

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def generate_schedules(staff_df, shift_config, start_date, end_date):
    """Generates daily shift schedules for all staff members."""
    schedules = []
    
    # Use the complex cycle from the config file
    cycle = shift_config['medical_shift_daily_cycle']
    cycle_len = len(cycle)
    
    # Assign a random starting point in the cycle to each staff member
    staff_cycle_start = {staff_id: random.randint(0, cycle_len - 1) for staff_id in staff_df['person_id']}

    current_date = start_date
    while current_date <= end_date:
        for _, staff_member in staff_df.iterrows():
            staff_id = staff_member['person_id']
            # Calculate the current day in the 24-day cycle for this staff member
            cycle_day_index = (staff_cycle_start[staff_id] + (current_date - start_date).days) % cycle_len
            shift_info = cycle[cycle_day_index]

            schedules.append({
                'staff_id': staff_id,
                'date': current_date.strftime('%Y-%m-%d'),
                'shift_name': shift_info['shift_type'],
                'is_work_day': shift_info['is_work_day'],
                'department': staff_member['Department']
            })
        
        # Log progress for every new month generated
        if current_date.day == 1:
            logging.info(f"Generated schedules for month: {current_date.strftime('%Y-%m')}")
        
        current_date += timedelta(days=1)
            
    return pd.DataFrame(schedules)

if __name__ == "__main__":
    logging.info("Generating staff schedules for the entire simulation period...")
    try:
        staff_df = pd.read_csv(STAFF_DATA_FILE)
        with open('/app/configs/hospital_shift_config.json', 'r') as f:
            shift_config = json.load(f)
        
        # Use the centrally defined simulation start and end dates
        schedule_df = generate_schedules(staff_df, shift_config, SIM_START_DATE, SIM_END_DATE)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(STAFF_SCHEDULES_FILE), exist_ok=True)
        
        schedule_df.to_csv(STAFF_SCHEDULES_FILE, index=False)
        logging.info(f"Finished generating schedules for {len(staff_df)} staff members. Saved to {STAFF_SCHEDULES_FILE}")

    except FileNotFoundError as e:
        logging.error(f"Required data file not found: {e}. Please ensure generate_staff.py has been run.")
    except Exception as e:
        logging.error(f"An unexpected error occurred while generating schedules: {e}")

