from datetime import datetime, timedelta
import os

# --- Simulation Timeline ---
SIM_START_DATE = datetime(2022, 11, 20)
REDUCED_PATIENT_PERIOD_START = datetime(2023, 7, 6)
NORMAL_PATIENT_PERIOD_RESUME = datetime(2024, 11, 13)
SIM_END_DATE = datetime(2025, 3, 31)

# --- Timing Control (in seconds) ---
BATCH_INTERVAL_SECONDS = 50    # 1 simulated day
STREAM_INTERVAL_SECONDS = 10   # ~8 simulated hours

# --- Population & Workforce Settings ---
POPULATION_SIZE = 3_000_000
STAFF_SIZE = 6_000
RESERVE_POOL_SIZE = 15_000
RETIREMENT_AGE = 64
WORKFORCE_SIM_INTERVAL = timedelta(days=90)

# --- Seasonal Patient Volumes ---
MONTHLY_PATIENT_LIMIT = 80_000
REDUCED_PATIENT_LIMIT = 60_000

FLU_PEAK_MONTHS = [4, 5, 6, 7, 8]
ACCIDENT_PEAK_MONTHS = [3, 4, 12]
BURN_PEAK_MONTHS = [5, 6, 7]
ASSAULT_PEAK_MONTHS = [12, 1]
ALCOHOL_PEAK_MONTHS = [9, 10, 11, 12]
POISONING_PEAK_MONTHS = [12, 1]
MALNUTRITION_PEAK_MONTHS = [6, 7, 8]

# --- Data Lake Paths (Use environment variables injected by Docker) ---
LAKE_PATH = os.getenv("LAKE_PATH", "/app/lake")
BATCH_DATA_PATH = os.path.join(LAKE_PATH, "batch")
STREAM_DATA_PATH = os.path.join(LAKE_PATH, "stream")
PROCESSED_DATA_PATH = os.path.join(LAKE_PATH, "processed")
FAILED_PATH = os.path.join(LAKE_PATH, "failed")
SETUP_FLAG_PATH = os.path.join(LAKE_PATH, ".setup_flags")
DAILY_FLAG_PATH = os.path.join(LAKE_PATH, ".daily_flags")

# --- Key Data Files ---
PEOPLE_DATA_FILE = os.path.join(PROCESSED_DATA_PATH, "people_data.csv")
STAFF_DATA_FILE = os.path.join(PROCESSED_DATA_PATH, "staff_data.csv")
RESERVE_POOL_FILE = os.path.join(PROCESSED_DATA_PATH, "reserve_pool.csv")
ILLNESSES_FILE = os.path.join(PROCESSED_DATA_PATH, "population_with_illnesses.csv")

# Schedules are dynamic — use month-based naming
SCHEDULES_PATH = PROCESSED_DATA_PATH

# --- Setup Completion Flags ---
PEOPLE_GENERATED_FLAG = os.path.join(SETUP_FLAG_PATH, "people_generated.flag")
STAFF_GENERATED_FLAG = os.path.join(SETUP_FLAG_PATH, "staff_generated.flag")
ILLNESSES_ASSIGNED_FLAG = os.path.join(SETUP_FLAG_PATH, "illnesses_assigned.flag")
WORKFORCE_SIMULATED_FLAG = os.path.join(SETUP_FLAG_PATH, "workforce_simulated.flag")
SCHEDULES_GENERATED_FLAG = os.path.join(SETUP_FLAG_PATH, "schedules_generated.flag")
INITIAL_DATA_GENERATED_FLAG = os.path.join(LAKE_PATH, "initial_data_generated.flag")

# --- Daily Flags (templated) ---
DAILY_VISITORS_FLAG_TPL = os.path.join(DAILY_FLAG_PATH, "visitors_{date}.flag")
DAILY_ADMISSIONS_FLAG_TPL = os.path.join(DAILY_FLAG_PATH, "admissions_{date}.flag")
DAILY_TRANSPORT_FLAG_TPL = os.path.join(DAILY_FLAG_PATH, "transport_{date}_session_{session}.flag")
DAILY_TRANSFERS_FLAG_TPL = os.path.join(DAILY_FLAG_PATH, "transfers_{date}_session_{session}.flag")
