import pandas as pd
import random
import os
import logging
import math
import uuid

# Import shared configuration and utilities
from simulation_config import PEOPLE_DATA_FILE, STAFF_DATA_FILE, RESERVE_POOL_FILE, RESERVE_POOL_SIZE
from utils import calculate_age, classify_experience

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# --- Configuration Data ---
STAFF_VACANCY_DATA = {
    "Medical": {"Filled": 759},
    "Allied Health": {"Filled": 552},
    "Nursing": {"Filled": 2187},
    "Admin & Support": {"Filled": 1397}
}
ROLE_AGE_LIMITS = {
    "Doctor": 27, "Nurse": 23, "Paramedic": 22, "Admin": 19, "Support Services": 19,
    "Pathologist": 27, "Pharmacist": 23, "Dental Assistant": 22, "Physiotherapist": 23,
    "Anesthesiologist": 23, "Radiographer": 21, "Occupational Therapist": 25,
    "Speech Therapist": 25, "EMT": 20, "Respiratory Therapist": 25, "Dietitian": 23,
    "Exercise Physiologist": 22, "Dental Hygienist": 25, "Radiation Therapist": 25,
    "Laboratory Technician": 25, "Security": 19, "Cleaning": 19, "Porter": 19, "Surgeon": 28
}

def sample_staff(df, role, num_to_sample, min_age):
    """Helper to sample eligible people for a specific role."""
    eligible_df = df[df['Age'] >= min_age]
    num_to_sample = min(num_to_sample, len(eligible_df))
    if num_to_sample == 0: return pd.DataFrame()
    sampled_df = eligible_df.sample(n=num_to_sample).copy()
    sampled_df['Role'] = role
    return sampled_df

def generate_staff_and_reserve(people_df, reserve_size):
    """Generates a detailed active staff roster and a reserve pool based on vacancy data."""
    logging.info("Generating detailed staff roster and reserve pool...")
    available_population = people_df.copy()
    available_population['Age'] = available_population['Birthdate'].apply(calculate_age)
    
    active_staff_list = []
    for role_group, vacancy_info in STAFF_VACANCY_DATA.items():
        num_to_fill_total = vacancy_info["Filled"]
        roles = {
            "Medical": ["Doctor", "Surgeon"],
            "Nursing": ["Nurse"],
            "Allied Health": ["Pathologist", "Pharmacist", "Dental Assistant", "Physiotherapist", "Anesthesiologist", "Radiographer", "Occupational Therapist", "Speech Therapist", "EMT", "Respiratory Therapist", "Dietitian", "Exercise Physiologist", "Dental Hygienist", "Radiation Therapist", "Laboratory Technician"],
            "Admin & Support": ["Admin", "Security", "Cleaning", "Porter"]
        }.get(role_group, [])
        
        num_per_role = math.ceil(num_to_fill_total / len(roles)) if roles else 0
        for role in roles:
            min_age = ROLE_AGE_LIMITS.get(role, 19)
            staff_for_role = sample_staff(available_population, role, num_per_role, min_age)
            if not staff_for_role.empty:
                active_staff_list.append(staff_for_role)
                available_population.drop(staff_for_role.index, inplace=True)

    active_staff_df = pd.concat(active_staff_list, ignore_index=True)
    
    # Sample the reserve pool to respect the configured size
    eligible_reserve = available_population[available_population['Age'] >= 18]
    num_to_sample_reserve = min(reserve_size, len(eligible_reserve))
    reserve_staff_df = eligible_reserve.sample(n=num_to_sample_reserve).copy()

    # Assign unique Staff_ID, Years_of_Service, and Experience_Level to both dataframes
    for df in [active_staff_df, reserve_staff_df]:
        df['Staff_ID'] = [str(uuid.uuid4()) for _ in range(len(df))]
        df['Years_of_Service'] = df.apply(
            lambda row: random.randint(0, max(0, row['Age'] - ROLE_AGE_LIMITS.get(row.get('Role'), 19))),
            axis=1
        )
        df['Experience_Level'] = df['Years_of_Service'].apply(classify_experience)

    # Assign a department to all active staff
    departments = ['Emergency', 'ICU', 'Surgery', 'Pediatrics', 'Oncology', 'Administration', 'Facilities']
    active_staff_df['Department'] = [random.choice(departments) for _ in range(len(active_staff_df))]

    # Also assign a placeholder department to the reserve pool for consistency
    reserve_staff_df['Department'] = 'Reserve'

    logging.info(f"Generated {len(active_staff_df)} active staff and {len(reserve_staff_df)} reserve staff.")
    return active_staff_df, reserve_staff_df

if __name__ == "__main__":
    try:
        people_df = pd.read_csv(PEOPLE_DATA_FILE)
        # Pass the RESERVE_POOL_SIZE from the config into the function
        active_staff_df, reserve_staff_df = generate_staff_and_reserve(people_df, RESERVE_POOL_SIZE)
        
        active_staff_df.to_csv(STAFF_DATA_FILE, index=False)
        reserve_staff_df.to_csv(RESERVE_POOL_FILE, index=False)
        
        logging.info(f"Initial staff data saved to {STAFF_DATA_FILE}")
        logging.info(f"Reserve pool data saved to {RESERVE_POOL_FILE}")
    except FileNotFoundError:
        logging.error(f"'{PEOPLE_DATA_FILE}' not found. Please ensure it has been generated first.")
    except Exception as e:
        logging.error(f"An error occurred in generate_staff.py: {e}", exc_info=True)
