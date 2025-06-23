# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the main scheduler script into the container.
# The COPY and RUN steps for requirements.txt are no longer needed.
COPY scheduler/scheduler.py .

# When the container starts, it will run the scheduler script
CMD ["python", "scheduler.py"]
