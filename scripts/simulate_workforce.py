import pandas as pd
import random
import uuid
import os
import logging
from datetime import datetime, timedelta

from simulation_config import SIM_START_DATE, SIM_END_DATE, PEOPLE_DATA_FILE, BATCH_DATA_PATH
from utils import calculate_age, classify_experience

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

RETIREMENT_AGE = 64
RESERVE_POOL_SIZE = 10000
QUARTERLY_INTERVAL = timedelta(days=90)

# Define initial staff numbers per category for the simulation start
# These numbers are based on the vacancy data in the original notebook
INITIAL_STAFF_NUMBERS = {
    "Medical": 759,
    "Allied Health": 352,
    "Nursing": 2187,
    "Admin & Support": 1597
}

def sample_staff(population_df, num_required, min_age=18):
    """Samples a specified number of staff from the eligible population."""
    eligible_staff = population_df[population_df['Age'] >= min_age].copy()
    
    # Ensure we don't try to sample more than available
    num_to_sample = min(num_required, len(eligible_staff))
    if num_to_sample == 0:
        return pd.DataFrame()
        
    return eligible_staff.sample(n=num_to_sample)

def create_initial_workforce(people_df):
    """Creates the initial active staff and a reserve pool."""
    logging.info("Creating initial workforce and reserve pool...")
    
    # Ensure 'Age' column exists
    if 'Age' not in people_df.columns:
        people_df['Age'] = people_df['Birthdate'].apply(calculate_age)

    # Sample staff for each category
    medical_staff = sample_staff(people_df, INITIAL_STAFF_NUMBERS["Medical"], 27)
    allied_health = sample_staff(people_df, INITIAL_STAFF_NUMBERS["Allied Health"], 22)
    nursing = sample_staff(people_df, INITIAL_STAFF_NUMBERS["Nursing"], 21)
    admin_support = sample_staff(people_df, INITIAL_STAFF_NUMBERS["Admin & Support"], 18)
    
    active_staff_df = pd.concat([medical_staff, allied_health, nursing, admin_support], ignore_index=True)
    
    # Add initial role-related data
    active_staff_df['Staff_ID'] = [str(uuid.uuid4()) for _ in range(len(active_staff_df))]
    active_staff_df['Years_of_Service'] = active_staff_df.apply(
        lambda row: random.randint(1, max(1, row['Age'] - 20)), axis=1
    )
    active_staff_df['Experience_Level'] = active_staff_df['Years_of_Service'].apply(classify_experience)

    # Create a reserve pool from the remaining population
    remaining_population = people_df.drop(active_staff_df.index)
    reserve_pool_df = sample_staff(remaining_population, RESERVE_POOL_SIZE)

    logging.info(f"Initial active staff: {len(active_staff_df)}, Reserve pool: {len(reserve_pool_df)}")
    return active_staff_df, reserve_pool_df

def run_workforce_update(active_staff_df, reserve_pool_df, current_date):
    """Runs a single quarterly update of the workforce."""
    logging.info(f"--- Running Workforce Update for {current_date.strftime('%Y-%m-%d')} ---")
    
    # Update Age and Years of Service for all staff
    active_staff_df['Age'] = active_staff_df['Birthdate'].apply(lambda bd: calculate_age(bd, today_str=current_date.strftime('%Y-%m-%d')))
    active_staff_df['Years_of_Service'] += 0.25 # Add a quarter of a year
    active_staff_df['Experience_Level'] = active_staff_df['Years_of_Service'].apply(classify_experience)

    # Identify retirements
    age_retirements = active_staff_df['Age'] >= RETIREMENT_AGE
    
    # Probabilistic early retirement
    early_retirement_chance = 0.01 # 1% chance per quarter
    early_retirement_mask = (active_staff_df['Years_of_Service'] >= 25) & (pd.Series(np.random.rand(len(active_staff_df))) < early_retirement_chance)
    
    retired_mask = age_retirements | early_retirement_mask
    retired_staff_df = active_staff_df[retired_mask]
    active_staff_df = active_staff_df[~retired_mask] # Keep non-retired staff

    num_retired = len(retired_staff_df)
    logging.info(f"Total staff retired this quarter: {num_retired}")

    # Replace retired staff from reserve pool
    if num_retired > 0:
        num_to_replace = min(num_retired, len(reserve_pool_df))
        if num_to_replace > 0:
            replacements = reserve_pool_df.head(num_to_replace)
            reserve_pool_df = reserve_pool_df.iloc[num_to_replace:]
            
            # Initialize new staff members' data
            replacements['Years_of_Service'] = 0
            replacements['Experience_Level'] = 'Junior'
            
            active_staff_df = pd.concat([active_staff_df, replacements], ignore_index=True)
            logging.info(f"Hired {num_to_replace} replacements from the reserve pool.")
        else:
            logging.warning("Reserve pool is empty. Cannot hire replacements.")

    return active_staff_df, reserve_pool_df

if __name__ == "__main__":
    logging.info("Starting workforce simulation...")
    try:
        people_df = pd.read_csv(PEOPLE_DATA_FILE)
        active_staff, reserve_pool = create_initial_workforce(people_df)

        current_date = SIM_START_DATE
        while current_date <= SIM_END_DATE:
            active_staff, reserve_pool = run_workforce_update(active_staff, reserve_pool, current_date)
            
            # Save a snapshot of the active staff for this quarter
            output_path = f"{BATCH_DATA_PATH}/staff_active_{current_date.strftime('%Y-%m-%d')}.csv"
            active_staff.to_csv(output_path, index=False)
            logging.info(f"Saved active staff snapshot to {output_path}")
            
            current_date += QUARTERLY_INTERVAL

        logging.info("Workforce simulation complete.")

    except FileNotFoundError:
        logging.error(f"{PEOPLE_DATA_FILE} not found. Please run generate_people_csv.py first.")
    except Exception as e:
        logging.error(f"An unexpected error occurred during workforce simulation: {e}")
