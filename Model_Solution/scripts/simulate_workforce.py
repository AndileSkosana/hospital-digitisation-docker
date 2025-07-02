import pandas as pd
import random
import os
import logging
from datetime import datetime, timedelta
import numpy as np

# Import shared configuration and utilities
from simulation_config import (
    SIM_START_DATE, SIM_END_DATE, STAFF_DATA_FILE, RESERVE_POOL_FILE,
    RETIREMENT_AGE, WORKFORCE_SIM_INTERVAL, BATCH_DATA_PATH
)
from utils import calculate_age, classify_experience

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def hire_replacements(retiring_staff_df, reserve_pool_df):
    """
    Hires replacements from the reserve pool, trying to match experience level.
    """
    new_hires_list = []
    
    for _, retiree in retiring_staff_df.iterrows():
        required_exp_level = retiree['Experience_Level']
        potential_replacements = reserve_pool_df[reserve_pool_df['Experience_Level'] == required_exp_level]
        
        if not potential_replacements.empty:
            new_hire = potential_replacements.head(1)
            new_hires_list.append(new_hire)
            reserve_pool_df.drop(new_hire.index, inplace=True)
        else:
            if not reserve_pool_df.empty:
                new_hire = reserve_pool_df.head(1)
                new_hires_list.append(new_hire)
                reserve_pool_df.drop(new_hire.index, inplace=True)
                logging.warning(f"Could not find a '{required_exp_level}' replacement. Hired a '{new_hire.iloc[0]['Experience_Level']}' instead.")
    
    if not new_hires_list:
        return pd.DataFrame(), reserve_pool_df

    return pd.concat(new_hires_list, ignore_index=True), reserve_pool_df


def simulate_workforce_evolution(active_staff_df, reserve_pool_df):
    """
    Simulates retirements and hiring over the entire simulation period,
    saving a snapshot of the active staff and a summary text file for each quarter.
    """
    logging.info("Starting workforce evolution simulation...")
    
    # --- Use more memory-efficient data types ---
    for col in ['Role', 'Department', 'Experience_Level', 'Gender', 'Race']:
        if col in active_staff_df.columns:
            active_staff_df[col] = active_staff_df[col].astype('category')
        if col in reserve_pool_df.columns:
            reserve_pool_df[col] = reserve_pool_df[col].astype('category')
    
    current_date = SIM_START_DATE
    while current_date <= SIM_END_DATE:
        # Update Staff Ages and Experience
        active_staff_df['Age'] = active_staff_df['Birthdate'].apply(lambda bd: calculate_age(bd, today_str=current_date.strftime('%Y-%m-%d')))
        active_staff_df['Years_of_Service'] += 0.25
        active_staff_df['Experience_Level'] = active_staff_df['Years_of_Service'].apply(classify_experience).astype('category')

        # Identify Retirements
        retire_mask = (active_staff_df['Age'] >= RETIREMENT_AGE) | \
                      ((active_staff_df['Years_of_Service'] >= 25) & (np.random.rand(len(active_staff_df)) < 0.01))
        
        retiring_staff = active_staff_df[retire_mask]
        num_retired = len(retiring_staff)
        
        num_hired = 0
        if num_retired > 0:
            active_staff_df = active_staff_df[~retire_mask]
            new_hires_df, reserve_pool_df = hire_replacements(retiring_staff, reserve_pool_df)
            num_hired = len(new_hires_df)
            if num_hired > 0:
                active_staff_df = pd.concat([active_staff_df, new_hires_df], ignore_index=True)

        # Generate Summary and Save Snapshots
        nearing_retirement_df = active_staff_df[active_staff_df['Age'].between(RETIREMENT_AGE - 3, RETIREMENT_AGE - 1)]
        upcoming_retirements_count = len(nearing_retirement_df)
        next_retiree_info = "None"
        if not nearing_retirement_df.empty:
            next_retiree = nearing_retirement_df.sort_values(by='Age', ascending=False).iloc[0]
            next_retiree_info = f"{next_retiree['First_Name']} {next_retiree['Surname']} (Age: {int(next_retiree['Age'])})"

        summary_text = f"""
Workforce Summary for Quarter Ending: {current_date.strftime('%Y-%m-%d')}
=========================================================
- Staff Retired This Quarter: {num_retired}
- New Replacements Hired: {num_hired}
- Current Reserve Pool Size: {len(reserve_pool_df)}
--- Retirement Outlook ---
- Staff Nearing Retirement (Next 3 Years): {upcoming_retirements_count}
- Next Likely Retiree (by age): {next_retiree_info}
"""
        with open(f"{BATCH_DATA_PATH}/workforce_summary_{current_date.strftime('%Y-%m-%d')}.txt", 'w') as f:
            f.write(summary_text)

        active_staff_df.to_csv(f"{BATCH_DATA_PATH}/staff_active_{current_date.strftime('%Y-%m-%d')}.csv", index=False)
        logging.info(f"On {current_date.date()}: Retired {num_retired}, Hired {num_hired}. Snapshot and summary saved.")
        
        current_date += WORKFORCE_SIM_INTERVAL
        
    logging.info("Workforce evolution simulation complete.")

if __name__ == "__main__":
    try:
        # --- Specify memory-efficient dtypes on load ---
        dtype_spec = {'Role': 'category', 'Department': 'category', 'Experience_Level': 'category', 'Gender': 'category', 'Race': 'category'}
        initial_staff_df = pd.read_csv(STAFF_DATA_FILE, dtype=dtype_spec)
        initial_reserve_df = pd.read_csv(RESERVE_POOL_FILE, dtype=dtype_spec)
        
        simulate_workforce_evolution(initial_staff_df, initial_reserve_df)
    except FileNotFoundError as e:
        logging.error(f"Required data file not found: {e}. Please ensure generate_staff.py has been run successfully.")
    except Exception as e:
        logging.error(f"An error occurred in simulate_workforce.py: {e}", exc_info=True)
