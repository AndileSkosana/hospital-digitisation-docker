# Use an official Python runtime as a parent image
FROM python:3.11-slim

WORKDIR /app

# Copy requirements from the service's directory
COPY batch_ingestor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files from the service's directory
COPY batch_ingestor/batch_ingestor.py .
COPY batch_ingestor/db_schema.sql .

# Copy the shared config file from the scripts directory
COPY scripts/simulation_config.py .

# The CMD instruction makes this a long-running service
CMD ["python", "batch_ingestor.py"]
