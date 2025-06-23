from datetime import datetime, timedelta

# --- Simulation Timeline & Pacing ---
SIM_START_DATE = datetime(2020, 12, 1)
SIM_END_DATE = datetime(2025, 3, 31)

# Real-world time intervals for jobs in seconds
BATCH_INTERVAL_SECONDS = 900  # 15 minutes
STREAM_INTERVAL_SECONDS = 180 # 3 minutes

# --- Data Generation Parameters ---
POPULATION_SIZE = 10000 

# --- Workforce Simulation Parameters ---
RETIREMENT_AGE = 64
RESERVE_POOL_SIZE = 10000
WORKFORCE_SIM_INTERVAL = timedelta(days=90) 

# --- File Paths ---
LAKE_PATH = '/app/shared_data' # Correctly points to your shared data directory
BATCH_DATA_PATH = f'{LAKE_PATH}/batch'
STREAM_DATA_PATH = f'{LAKE_PATH}/stream'

# Initial setup files
PEOPLE_DATA_FILE = f'{BATCH_DATA_PATH}/people_data.csv'
ILLNESSES_FILE = f'{BATCH_DATA_PATH}/population_with_illnesses.csv'
STAFF_SCHEDULES_FILE = f'{BATCH_DATA_PATH}/staff_schedules.csv'
WORKFORCE_SNAPSHOT_PATH = BATCH_DATA_PATH 

# Flag file to check if initial setup is complete
INITIAL_DATA_FLAG_FILE = f'{LAKE_PATH}/initial_data_complete.flag'
