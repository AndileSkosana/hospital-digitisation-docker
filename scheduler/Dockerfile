# Use a modern, stable Python runtime
FROM python:3.11-slim

# Set a single, clean working directory
WORKDIR /app

# Copy and install requirements for all scripts run by the scheduler
COPY scheduler/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all required scripts into the same flat directory
# This ensures they can all find each other for imports and execution.
COPY scheduler/scheduler.py .
COPY scripts/simulation_config.py .
COPY scripts/utils.py .
COPY scripts/generate_people.py .
COPY scripts/assign_illnesses.py .
COPY scripts/simulate_workforce.py .
COPY scripts/generate_staff_schedules.py .
COPY scripts/generate_patients.py .
COPY scripts/generate_patient_admissions.py .
COPY scripts/generate_patient_transfers.py .
COPY scripts/generate_emergency_transport.py .
COPY scripts/generate_hospital_summary.py .

# The CMD instruction runs the main scheduler script from /app
CMD ["python", "scheduler.py"]