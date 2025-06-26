import time
import subprocess
import logging
import json
import os
import signal
import shutil
import threading
import sys
from datetime import datetime, timedelta

# Import all necessary constants, including the daily flag templates
from simulation_config import (
    SIM_START_DATE, SIM_END_DATE, BATCH_INTERVAL_SECONDS,
    SETUP_FLAG_PATH, PEOPLE_GENERATED_FLAG, ILLNESSES_ASSIGNED_FLAG,
    STAFF_GENERATED_FLAG, WORKFORCE_SIMULATED_FLAG, SCHEDULES_GENERATED_FLAG,
    DAILY_FLAG_PATH, DAILY_VISITORS_FLAG_TPL, DAILY_ADMISSIONS_FLAG_TPL
)

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
STATE_FILE = '/app/shared_data/scheduler_state.json' 
simulation_running = True

# --- Global State & Threading Lock ---
state_lock = threading.Lock()
current_sim_date = SIM_START_DATE

def save_state():
    """Saves the current state of the simulation."""
    with state_lock:
        state = {'current_sim_date': current_sim_date.strftime('%Y-%m-%d')}
        if os.path.exists(STATE_FILE):
            backup_path = f'{STATE_FILE}.bak.{datetime.now().strftime("%Y%m%dT%H%M%S")}'
            try:
                shutil.copy(STATE_FILE, backup_path)
            except Exception as e:
                logging.warning(f"Could not create state backup: {e}")
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        logging.info(f"State saved for date: {current_sim_date.strftime('%Y-%m-%d')}")

def load_state():
    """Loads the simulation state from a file."""
    global current_sim_date
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
            with state_lock:
                current_sim_date = datetime.strptime(state['current_sim_date'], '%Y-%m-%d')
            logging.info(f"Resumed simulation from date: {current_sim_date.strftime('%Y-%m-%d')}")
        except Exception as e:
            logging.warning(f"State file error: {e}. Starting fresh.")
    else:
        logging.info("No state file found. Starting from the beginning.")

def handle_shutdown(signum, frame):
    """Gracefully handle shutdown signals."""
    global simulation_running
    logging.info("Shutdown signal received. Saving state...")
    simulation_running = False
    save_state()
    
def run_script(script_name, *args):
    """Executes a given Python script and returns True on success, False on failure."""
    command = ['python', script_name] + list(args)
    logging.info(f"Executing: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True, timeout=1800, cwd='/app/scripts')
        if result.stdout: logging.info(f"Output from {script_name}:\n{result.stdout.strip()}")
        if result.stderr: logging.warning(f"Stderr from {script_name}:\n{result.stderr.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Script '{script_name}' failed with exit code {e.returncode}.")
        logging.error(f"Stdout from failed script:\n{e.stdout}")
        logging.error(f"Stderr from failed script:\n{e.stderr}")
        return False
    except Exception as e:
        logging.exception(f"An unexpected error occurred while running {script_name}: {e}")
        return False

def daily_simulation_cycle():
    """
    Runs the full sequence of data generation for a single simulated day,
    using daily flags to ensure each step completes successfully.
    """
    global current_sim_date
    with state_lock:
        if current_sim_date > SIM_END_DATE: return
        sim_date_str = current_sim_date.strftime('%Y-%m-%d')
    
    logging.info(f"--- Processing Simulated Day: {sim_date_str} ---")

    # Define daily flags using the templates from the config
    visitors_flag = DAILY_VISITORS_FLAG_TPL.format(date=sim_date_str)
    admissions_flag = DAILY_ADMISSIONS_FLAG_TPL.format(date=sim_date_str)

    # Step 1: Generate the list of daily visitors if not already done
    if not os.path.exists(visitors_flag):
        if run_script('generate_patients.py', sim_date_str):
            with open(visitors_flag, 'w') as f: f.write(datetime.now().isoformat())
            logging.info(f"Visitor generation complete for {sim_date_str}")
        else:
            logging.error(f"Could not generate daily visitors for {sim_date_str}. Skipping day.")
            return # Skip the rest of the day's processing

    # Step 2: Stream emergency transport and transfers
    # These are quick tasks and don't need their own flags for this design
    run_script('generate_emergency_transport.py', sim_date_str)
    previous_day_str = (current_sim_date - timedelta(days=1)).strftime('%Y-%m-%d')
    run_script('generate_patient_transfers.py', previous_day_str)

    # Step 3: Run the admissions process if not already done
    if not os.path.exists(admissions_flag):
        if run_script('generate_patient_admissions.py', sim_date_str):
            with open(admissions_flag, 'w') as f: f.write(datetime.now().isoformat())
            logging.info(f"Admissions processing complete for {sim_date_str}")
        else:
            logging.error(f"Could not process admissions for {sim_date_str}. Skipping day.")
            return

    # Advance to the next day only if all steps for the current day are complete
    with state_lock:
        current_sim_date += timedelta(days=1)
    save_state()

def scheduler_loop():
    """Main scheduler loop that runs the daily simulation cycle."""
    while simulation_running and current_sim_date <= SIM_END_DATE:
        daily_simulation_cycle()
        logging.info(f"--- Day complete. Waiting for {BATCH_INTERVAL_SECONDS} seconds... ---")
        time.sleep(BATCH_INTERVAL_SECONDS)
    logging.info("--- Simulation Period Finished ---")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    logging.info("--- Hospital Data Warehouse Simulation Starting ---")
    
    os.makedirs(SETUP_FLAG_PATH, exist_ok=True)
    os.makedirs(DAILY_FLAG_PATH, exist_ok=True)
    
    # --- Initial Setup with Granular Flags ---
    initial_setup_steps = [
        ('generate_people.py', PEOPLE_GENERATED_FLAG, 'base population'),
        ('assign_illnesses.py', ILLNESSES_ASSIGNED_FLAG, 'illnesses'),
        ('generate_staff.py', STAFF_GENERATED_FLAG, 'initial staff roster'),
        ('simulate_workforce.py', WORKFORCE_SIMULATED_FLAG, 'workforce evolution'),
        ('generate_staff_schedules.py', SCHEDULES_GENERATED_FLAG, 'staff schedules')
    ]
    
    for i, (script, flag_file, description) in enumerate(initial_setup_steps):
        step_num = i + 1
        if not os.path.exists(flag_file):
            logging.info(f"--- Step {step_num}/{len(initial_setup_steps)}: Generating {description}... ---")
            if run_script(script):
                with open(flag_file, 'w') as f: f.write(datetime.now().isoformat())
                logging.info(f"Step {step_num}/{len(initial_setup_steps)} complete.")
            else:
                logging.fatal(f"Fatal Error: Could not generate {description}. Halting.")
                sys.exit(1)
        else:
            logging.info(f"--- Step {step_num}/{len(initial_setup_steps)}: {description.capitalize()} already exist. Skipping. ---")

    logging.info("--- All initial data generation steps complete. ---")
    
    load_state()
    scheduler_loop()

    logging.info("Scheduler loop has exited. Application will now shut down.")
    sys.exit(0)
