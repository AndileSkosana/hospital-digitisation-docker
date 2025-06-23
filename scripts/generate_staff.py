import pandas as pd
import random
import os
import logging
from simulation_config import STAFF_SIZE, PEOPLE_DATA_FILE, STAFF_DATA_FILE
from utils import calculate_age

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def assign_staff_roles(people_df, num_staff):
    """Assigns roles and departments to a sample of the population to create staff."""
    # Ensure we only select adults for staff roles
    people_df['Age'] = people_df['Birthdate'].apply(calculate_age)
    eligible_people = people_df[people_df['Age'] >= 18]
    
    staff_df = eligible_people.sample(n=min(num_staff, len(eligible_people)))
    
    roles = ['Doctor', 'Nurse', 'Admin', 'Paramedic', 'Surgeon', 'Dietician', 'Support Staff']
    departments = ['Emergency', 'ICU', 'Surgery', 'Pediatrics', 'Oncology', 'Administration', 'Facilities']
    
    assigned_roles = [random.choice(roles) for _ in range(len(staff_df))]
    assigned_depts = [random.choice(departments) for _ in range(len(staff_df))]
    
    staff_df = staff_df.copy()
    staff_df.loc[:, 'Role'] = assigned_roles
    staff_df.loc[:, 'Department'] = assigned_depts
    
    return staff_df

if __name__ == "__main__":
    logging.info("Generating initial staff data...")
    try:
        people_df = pd.read_csv(PEOPLE_DATA_FILE)
        staff_df = assign_staff_roles(people_df, STAFF_SIZE)
        staff_df.to_csv(STAFF_DATA_FILE, index=False)
        logging.info(f"Finished generating staff data. Saved to {STAFF_DATA_FILE}")
    except FileNotFoundError:
        logging.error(f"{PEOPLE_DATA_FILE} not found. Please run generate_people_csv.py first.")
