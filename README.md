# Hospital Digitisation Project

## Overview
This project aims to digitise and consolidate hospital records for a major public hospital in Johannesburg. As a data engineering initiative, it involves the streaming and batch ingestion of hospital records and the updating of a modern data warehouse.

## Project Structure
The project is organized into several directories and files, each serving a specific purpose:

```
hospital-data-project
├── docker-compose.yml          # Defines services, networks, and volumes for Docker containers
├── .env                        # Environment variables for configuration
├── shared_data                 # Contains generated data files
│   ├── people.csv              # Synthetic population data
│   ├── doctors.csv             # Data for doctors, including specialties
│   ├── hospital_patients.csv    # Data for hospital patients and medical records
│   ├── staff_assignments.csv    # Assignments of hospital staff
├── producer                     # Contains files for the data producer service
│   ├── Dockerfile               # Instructions to build the producer Docker image
│   ├── app.py                  # Main application script for data generation
│   ├── utils.py                # Utility functions for data generation
├── batch_ingestor               # Contains files for the batch ingestor service
│   ├── Dockerfile               # Instructions to build the batch ingestor Docker image
│   └── batch_ingest.py         # Logic for reading CSVs and updating PostgreSQL
├── stream_processor             # Contains files for the stream processor service
│   ├── Dockerfile               # Instructions to build the stream processor Docker image
│   └── stream_producer.py      # Simulates streaming data ingestion
├── scheduler                    # Contains files for the scheduler service
│   ├── Dockerfile               # Instructions to build the scheduler Docker image
│   └── scheduler.py            # Logic for scheduling batch and stream processing
├── postgres                     # Contains database initialization scripts
│   └── init_db.sql             # SQL commands to initialize the database schema
├── pgadmin                      # Configuration for pgAdmin
├── README.md                   # Documentation for the project
└── project_brief.pdf           # Detailed overview of the project
```

## Getting Started

### Prerequisites
- Docker
- Docker Compose

### Setup Instructions
1. **Clone the Repository**
   ```
   git clone <your-repo-url>
   cd hospital-data-project
   ```

2. **Build and Start the System**
   ```
   docker-compose up --build
   ```
   This command will start the following services:
   - PostgreSQL + pgAdmin
   - Producer (CSV generator)
   - Batch and stream processors
   - Scheduler

3. **View Outputs**
   - All generated CSV files will be located in the `shared_data/` folder.
   - To view the database contents, navigate to `http://localhost:5050` and log into pgAdmin using the credentials specified in the `.env` or `docker-compose.yml` files.

### Configuration
Modify the `.env` file to change the following parameters:
- `NUM_PEOPLE`: Number of synthetic people to generate (default: 5000000)
- `START_DATE`: Start date for the data (default: 2020-01-01)
- `END_DATE`: End date for the data (default: 2025-12-31)
- `DATA_FOLDER`: Path for storing generated data (default: /app/shared_data)

### Troubleshooting
If you encounter issues with container volumes, try the following commands:
```
docker-compose down -v
docker-compose up --build
```
Ensure that the `shared_data/` directory exists before starting the system.

## Conclusion
This project provides a comprehensive approach to hospital digitisation through data engineering practices, including data ingestion, processing, and storage. For further details, refer to the `project_brief.pdf`.