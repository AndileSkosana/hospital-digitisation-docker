from datetime import datetime, timedelta

# --- Simulation Timeline & Pacing ---
SIM_START_DATE = datetime(2020, 12, 1)
SIM_END_DATE = datetime(2025, 3, 31)

# Real-world time intervals for jobs in seconds
BATCH_INTERVAL_SECONDS = 900  # 15 minutes
STREAM_INTERVAL_SECONDS = 180 # 3 minutes

# --- Data Generation Parameters ---
# Defines how many people records to generate initially
POPULATION_SIZE = 10000 

# --- Workforce Simulation Parameters ---
# The age at which staff are eligible for mandatory retirement
RETIREMENT_AGE = 64
# The size of the reserve pool for hiring replacements
RESERVE_POOL_SIZE = 10000
# The interval at which to run the workforce evolution (retirement/hiring) simulation
WORKFORCE_SIM_INTERVAL = timedelta(days=90) # Every 90 days (approx. 1 quarter)

# --- File Paths ---
# Centralized paths for data files within the shared lake volume
LAKE_PATH = '/app/shared_data'
BATCH_DATA_PATH = f'{LAKE_PATH}/batch'
STREAM_DATA_PATH = f'{LAKE_PATH}/stream'

# Initial setup files
PEOPLE_DATA_FILE = f'{BATCH_DATA_PATH}/people_data.csv'
ILLNESSES_FILE = f'{BATCH_DATA_PATH}/population_with_illnesses.csv'
STAFF_SCHEDULES_FILE = f'{BATCH_DATA_PATH}/staff_schedules.csv'

# Workforce simulation files
# This path will store the quarterly staff snapshots, e.g., staff_active_2020-12-01.csv
WORKFORCE_SNAPSHOT_PATH = BATCH_DATA_PATH 
