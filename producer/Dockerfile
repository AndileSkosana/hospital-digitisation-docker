# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements from the service's directory, relative to the build context
COPY producer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application script from the service's directory, relative to the build context
COPY producer/producer.py .