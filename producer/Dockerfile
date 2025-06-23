# Use a more modern and stable Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's layer caching.
# The dependency installation layer will only be rebuilt if requirements.txt changes.
COPY producer/requirements.txt .

# Install the Python dependencies from the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the producer script into the container
COPY producer/producer.py .
