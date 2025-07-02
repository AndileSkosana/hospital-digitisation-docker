# Use an official Python runtime as a parent image
FROM python:3.11-slim

WORKDIR /app

# Copy requirements from the service's directory
COPY stream_processor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application script from the service's directory
COPY stream_processor/stream_processor.py .

# Copy the shared config file from the scripts directory
COPY scripts/simulation_config.py .

# The CMD instruction makes this a long-running service
CMD ["python", "stream_processor.py"]
