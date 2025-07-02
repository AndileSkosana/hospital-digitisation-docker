import time
import subprocess
import logging
import json
import os
import signal
import shutil
import sys
from datetime import datetime, timedelta

# Import all necessary constants from the centralized config
from simulation_config import (
    SIM_START_DATE, SIM_END_DATE, STREAM_INTERVAL_SECONDS,
    SETUP_FLAG_PATH, PEOPLE_GENERATED_FLAG, ILLNESSES_ASSIGNED_FLAG,
    STAFF_GENERATED_FLAG, WORKFORCE_SIMULATED_FLAG, SCHEDULES_GENERATED_FLAG,
    DAILY_FLAG_PATH, DAILY_VISITORS_FLAG_TPL, DAILY_ADMISSIONS_FLAG_TPL,
    DAILY_TRANSPORT_FLAG_TPL, DAILY_TRANSFERS_FLAG_TPL
)

# Configuration
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
STATE_FILE = '/app/shared_data/scheduler_state.json' 
simulation_running = True

# Global State
current_sim_date = SIM_START_DATE

def save_state():
    """Saves the current state of the simulation."""
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

def retry_run_script(script_name, *args, retries=3, delay=5):
    """
    A wrapper for run_script that retries on failure.
    Useful for tasks that might have transient errors (e.g., network issues).
    """
    for i in range(retries):
        if run_script(script_name, *args):
            return True
        logging.warning(f"Attempt {i+1}/{retries} failed for {script_name}. Retrying in {delay} seconds...")
        time.sleep(delay)
    logging.error(f"All {retries} retries failed for {script_name}.")
    return False

def validate_daily_flags(sim_date_str, num_sessions=5):
    """Checks if all expected flags for a given day have been created."""
    expected_flags = [DAILY_VISITORS_FLAG_TPL.format(date=sim_date_str),
                      DAILY_ADMISSIONS_FLAG_TPL.format(date=sim_date_str)]
    
    previous_day_str = (datetime.strptime(sim_date_str, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')

    for i in range(1, num_sessions + 1):
        expected_flags.append(DAILY_TRANSPORT_FLAG_TPL.format(date=sim_date_str, session=i))
        expected_flags.append(DAILY_TRANSFERS_FLAG_TPL.format(date=previous_day_str, session=i))

    missing_flags = [flag for flag in expected_flags if not os.path.exists(flag)]
    
    if missing_flags:
        logging.warning(f"Validation failed for day {sim_date_str}. Missing flags: {missing_flags}")
        return False
    
    logging.info(f"All {len(expected_flags)} daily flags validated for {sim_date_str}.")
    return True


def daily_simulation_cycle():
    """
    Runs the full sequence of data generation for a single simulated day,
    including multiple streaming sessions in a sequential manner.
    """
    global current_sim_date
    
    if current_sim_date > SIM_END_DATE:
        global simulation_running
        simulation_running = False
        return

    sim_date_str = current_sim_date.strftime('%Y-%m-%d')
    logging.info(f"--- Processing Simulated Day: {sim_date_str} ---")

    visitors_flag = DAILY_VISITORS_FLAG_TPL.format(date=sim_date_str)
    if not os.path.exists(visitors_flag):
        if run_script('generate_patients.py', sim_date_str):
            with open(visitors_flag, 'w') as f: f.write(datetime.now().isoformat())
        else:
            logging.error(f"Could not generate daily visitors for {sim_date_str}. Skipping day.")
            return

    num_sessions = 5
    for session in range(num_sessions):
        if not simulation_running: break
        
        logging.info(f"--- Running Session {session + 1}/{num_sessions} for Day: {sim_date_str} ---")
        
        transport_flag = DAILY_TRANSPORT_FLAG_TPL.format(date=sim_date_str, session=session+1)
        if not os.path.exists(transport_flag):
            if retry_run_script('generate_emergency_transport.py', sim_date_str, str(session), str(num_sessions)):
                with open(transport_flag, 'w') as f: f.write(datetime.now().isoformat())
        
        previous_day_str = (current_sim_date - timedelta(days=1)).strftime('%Y-%m-%d')
        transfers_flag = DAILY_TRANSFERS_FLAG_TPL.format(date=previous_day_str, session=session+1)
        if not os.path.exists(transfers_flag):
            if retry_run_script('generate_patient_transfers.py', previous_day_str, str(session), str(num_sessions)):
                 with open(transfers_flag, 'w') as f: f.write(datetime.now().isoformat())
        
        time.sleep(STREAM_INTERVAL_SECONDS)

    if simulation_running:
        admissions_flag = DAILY_ADMISSIONS_FLAG_TPL.format(date=sim_date_str)
        if not os.path.exists(admissions_flag):
            logging.info(f"--- End of Day Batch Processing for: {sim_date_str} ---")
            if run_script('generate_patient_admissions.py', sim_date_str):
                with open(admissions_flag, 'w') as f: f.write(datetime.now().isoformat())

    # Validate all flags before advancing the day
    if validate_daily_flags(sim_date_str, num_sessions):
        logging.info(f"--- Day {sim_date_str} successfully completed and validated. ---")
        current_sim_date += timedelta(days=1)
        save_state()
    else:
        logging.error(f"Day {sim_date_str} did not complete successfully. It will be re-processed on the next cycle.")


def run_initial_setup():
    """Runs the entire one-time data generation sequence."""
    os.makedirs(SETUP_FLAG_PATH, exist_ok=True)
    os.makedirs(DAILY_FLAG_PATH, exist_ok=True)
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
            else:
                logging.fatal(f"Fatal Error: Could not generate {description}. Halting.")
                sys.exit(1)
        else:
            logging.info(f"--- Step {step_num}/{len(initial_setup_steps)}: {description.capitalize()} already exists. Skipping. ---")

    logging.info("--- All initial data generation steps complete. ---")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    logging.info("--- Hospital Data Warehouse Simulation Starting ---")
    
    run_initial_setup()
    
    load_state()

    while simulation_running:
        daily_simulation_cycle()
        if not simulation_running: break
        time.sleep(1) # Small sleep to prevent busy-waiting if a day finishes quickly

    logging.info("Scheduler loop has exited. Application will now shut down.")
    sys.exit(0)
