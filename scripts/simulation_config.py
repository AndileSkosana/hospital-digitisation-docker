from datetime import datetime, timedelta

# --- Simulation Timeline & Pacing ---
SIM_START_DATE = datetime(2022, 11, 20)
REDUCED_PATIENT_PERIOD_START = datetime(2024, 1, 6)
NORMAL_PATIENT_PERIOD_RESUME = datetime(2025, 2, 1)
SIM_END_DATE = datetime(2025, 3, 31)

# Real-world time intervals for jobs in seconds
BATCH_INTERVAL_SECONDS = 10  # 15 minutes
STREAM_INTERVAL_SECONDS = 10 # 3 minutes

# --- Data Generation Parameters ---
POPULATION_SIZE = 3000000 
STAFF_SIZE = 6000 # The size of the initial active staff roster

# --- Workforce Simulation Parameters ---
RETIREMENT_AGE = 64
# This is used by generate_staff.py to create the initial reserve pool size.
# simulate_workforce.py will then use the generated file.
RESERVE_POOL_SIZE = 15000 
WORKFORCE_SIM_INTERVAL = timedelta(days=90) 

# --- Patient Volume & Seasonality (from your notebook logic) ---
MONTHLY_PATIENT_LIMIT = 80000
REDUCED_PATIENT_LIMIT = 60000
FLU_PEAK_MONTHS = [4, 5, 6, 7, 8]
ACCIDENT_PEAK_MONTHS = [3, 4, 12]
BURN_PEAK_MONTHS = [5, 6, 7]
ASSAULT_PEAK_MONTHS = [12, 1]
ALCOHOL_PEAK_MONTHS = [9, 10, 11, 12]
POISONING_PEAK_MONTHS = [12, 1]
MALNUTRITION_PEAK_MONTHS = [6, 7, 8]

# --- File Paths ---
LAKE_PATH = '/app/shared_data'
BATCH_DATA_PATH = f'{LAKE_PATH}/batch'
STREAM_DATA_PATH = f'{LAKE_PATH}/stream'

# Initial setup data files
PEOPLE_DATA_FILE = f'{BATCH_DATA_PATH}/people_data.csv'
STAFF_DATA_FILE = f'{BATCH_DATA_PATH}/staff_data.csv'
RESERVE_POOL_FILE = f'{BATCH_DATA_PATH}/reserve_pool.csv'
ILLNESSES_FILE = f'{BATCH_DATA_PATH}/population_with_illnesses.csv'
STAFF_SCHEDULES_FILE = f'{BATCH_DATA_PATH}/staff_schedules.csv'
WORKFORCE_SNAPSHOT_PATH = BATCH_DATA_PATH 

# --- Granular Flag Files for Initial Setup ---
# A separate flag is created upon the successful completion of each major step.
SETUP_FLAG_PATH = f'{LAKE_PATH}/.setup_flags'
PEOPLE_GENERATED_FLAG = f'{SETUP_FLAG_PATH}/people_generated.flag'
STAFF_GENERATED_FLAG = f'{SETUP_FLAG_PATH}/staff_generated.flag'
ILLNESSES_ASSIGNED_FLAG = f'{SETUP_FLAG_PATH}/illnesses_assigned.flag'
WORKFORCE_SIMULATED_FLAG = f'{SETUP_FLAG_PATH}/workforce_simulated.flag'
SCHEDULES_GENERATED_FLAG = f'{SETUP_FLAG_PATH}/schedules_generated.flag'

# --- Daily Process Flags ---
# These are format strings to create a unique flag for each day's tasks.
# Example usage: DAILY_VISITORS_FLAG_TPL.format(date=sim_date_str)
DAILY_FLAG_PATH = f'{LAKE_PATH}/.daily_flags'
DAILY_VISITORS_FLAG_TPL = f'{DAILY_FLAG_PATH}/visitors_{{date}}.flag'
DAILY_ADMISSIONS_FLAG_TPL = f'{DAILY_FLAG_PATH}/admissions_{{date}}.flag'