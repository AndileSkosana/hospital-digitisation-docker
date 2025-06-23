import pandas as pd
import uuid
import random
import logging
import os
from faker import Faker
from datetime import datetime, timedelta
from utils import SA_NAMES, SURNAMES_BY_RACE, generate_gauteng_address
from simulation_config import POPULATION_SIZE, PEOPLE_DATA_FILE

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def generate_people(num_records):
    """Generates a DataFrame of synthetic people using detailed demographic data."""
    data = []
    races = list(SA_NAMES.keys())
    fake = Faker('en_ZA')

    for _ in range(num_records):
        race = random.choice(races)
        name_info = random.choice(SA_NAMES[race])
        birthdate = datetime.now() - timedelta(days=random.randint(365*1, 365*85))
        
        data.append({
            'person_id': str(uuid.uuid4()),
            'First_Name': name_info['name'],
            'Surname': random.choice(SURNAMES_BY_RACE[race]),
            'Gender': name_info['gender'],
            'Race': race,
            'Birthdate': birthdate.strftime('%Y-%m-%d'),
            'Residential_address': generate_gauteng_address()
        })
    return pd.DataFrame(data)

if __name__ == "__main__":
    logging.info("Generating base population data...")
    os.makedirs(os.path.dirname(PEOPLE_DATA_FILE), exist_ok=True)
    df = generate_people(POPULATION_SIZE)
    df.to_csv(PEOPLE_DATA_FILE, index=False)
    logging.info(f"Finished generating people data. Saved to {PEOPLE_DATA_FILE}")
