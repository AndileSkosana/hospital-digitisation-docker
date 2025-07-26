from datetime import datetime, timedelta

# --- Simulation Timeline & Pacing ---
SIM_START_DATE = datetime(2022, 11, 20)
REDUCED_PATIENT_PERIOD_START = datetime(2023, 7, 6)
NORMAL_PATIENT_PERIOD_RESUME = datetime(2024, 11, 13)
SIM_END_DATE = datetime(2025, 3, 31)

# Real-world time intervals for jobs in seconds
BATCH_INTERVAL_SECONDS = 50  # 15 minutes
STREAM_INTERVAL_SECONDS = 10 # 3 minutes

# --- Data Generation Parameters ---
POPULATION_SIZE = 3000000 
STAFF_SIZE = 6000 
RESERVE_POOL_SIZE = 15000 

# --- Workforce Simulation Parameters ---
RETIREMENT_AGE = 64
WORKFORCE_SIM_INTERVAL = timedelta(days=90) 

# --- Patient Volume & Seasonality ---
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
LAKE_PATH = '/app/shared_data'  # Path for all files
BATCH_DATA_PATH = f'{LAKE_PATH}/batch' # Path for batch files before being processed
FAILED_PATH = f'{LAKE_PATH}/failed' # Path for failed files
STREAM_DATA_PATH = f'{LAKE_PATH}/stream' # Path for stream files before being processed
PROCESSED_DATA_PATH = f'{LAKE_PATH}/processed' # Path for processed files after ingestion
SETUP_FLAG_PATH = f'{LAKE_PATH}/.setup_flags'  # Path for flag files

# These files are created in /batch but consumed from /processed by daily scripts.
PEOPLE_DATA_FILE = f'{PROCESSED_DATA_PATH}/people_data.csv' # Path for files after being processed
STAFF_DATA_FILE = f'{PROCESSED_DATA_PATH}/staff_data.csv' # Path for files after being processed
RESERVE_POOL_FILE = f'{PROCESSED_DATA_PATH}/reserve_pool.csv'# Path for files after being processed
ILLNESSES_FILE = f'{PROCESSED_DATA_PATH}/population_with_illnesses.csv'# Path for files after being processed
# Schedules are monthly, so the daily scripts will need to construct the correct path dynamically
SCHEDULES_PATH = PROCESSED_DATA_PATH  # Path for all schedule files after being processed

# Granular Flag Files for Initial Setup
PEOPLE_GENERATED_FLAG = f'{SETUP_FLAG_PATH}/people_generated.flag' # Path for population flag file
STAFF_GENERATED_FLAG = f'{SETUP_FLAG_PATH}/staff_generated.flag' # Path for staff flag file
ILLNESSES_ASSIGNED_FLAG = f'{SETUP_FLAG_PATH}/illnesses_assigned.flag' # Path for illnesses flag file
WORKFORCE_SIMULATED_FLAG = f'{SETUP_FLAG_PATH}/workforce_simulated.flag' # Path for workforce flag file
SCHEDULES_GENERATED_FLAG = f'{SETUP_FLAG_PATH}/schedules_generated.flag' # Path for schedule flag file
INITIAL_DATA_GENERATED_FLAG = f'{LAKE_PATH}/initial_data_generated.flag' # Path for setup flag file

# --- Daily Process Flags ---
DAILY_FLAG_PATH = f'{LAKE_PATH}/.daily_flags'  # Path for daily flag files
DAILY_VISITORS_FLAG_TPL = f'{DAILY_FLAG_PATH}/visitors_{{date}}.flag'  # Path for visitor flag files
DAILY_ADMISSIONS_FLAG_TPL = f'{DAILY_FLAG_PATH}/admissions_{{date}}.flag'  # Path for admission flag files
DAILY_TRANSPORT_FLAG_TPL = f'{DAILY_FLAG_PATH}/transport_{{date}}_session_{{session}}.flag' # Path for transport flag files
DAILY_TRANSFERS_FLAG_TPL = f'{DAILY_FLAG_PATH}/transfers_{{date}}_session_{{session}}.flag' # Path for transfer flag files