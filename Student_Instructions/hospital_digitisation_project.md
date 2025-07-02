# Hospital Digitisation Project

## 📘 Overview

Welcome to your first project as a data engineer – congratulations on reaching this milestone ⭐️!

You’ve just joined a consulting firm that’s been awarded a contract to digitise and consolidate hospital records for a major public hospital in Johannesburg. Your role is critical to this transformation. You’ll be working on streaming and batch ingestion of hospital records and helping update a modern data warehouse.

This project will simulate real-world data engineering scenarios involving data ingestion, data cleaning, and real-time database updates using Docker, PostgreSQL, and Kafka.

Your team lead wants to assess your technical abilities with this challenge over the next **9 days**. Your goal is to containerize and orchestrate this system using Docker Compose. You’ve got this! 💪

## 🧑‍⚕️ Project Objectives

- Build containers for all components
- Configure Kafka and PostgreSQL services
- Mount shared volumes for data exchange
- Execute Python scripts inside containers
- Persist batch and stream data in a shared lake

## 📊 Infrastructure Architecture

You will create **8 services** using Docker:

| Service          | Role                                  |
| ---------------- | ------------------------------------- |
| Kafka            | Stream platform                       |
| Zookeeper        | Kafka coordination                    |
| PostgreSQL       | Stores batch-ingested data            |
| pgAdmin          | Database GUI                          |
| Producer         | Publishes transfer/patient events     |
| Stream Processor | Writes Kafka events to `/lake/stream` |
| Batch Ingestor   | Reads batch files into PostgreSQL     |
| Scheduler        | Runs batch/stream scripts on schedule |

## 🗃️ Provided Files

You have been given:

```bash
/configs/                  # Kafka, DB, and hospital shift configuration
/scripts/                  # Python files for data generation and ingestion
/db/                       # PostgreSQL schema setup files
  └── db_schema.sql        # SQL schema to initialize the hospital database
/requirements.txt          # Required Python packages (for all services)
```

> You must create Dockerfiles for each container and orchestrate them with Docker Compose.

## ⚡ Versions and Constraints

To ensure consistency, the following versions are required for automated evaluation:

| Tool            | Version    |
| --------------- | ---------- |
| Python          | 3.11.8     |
| kafka-python    | 2.0.2      |
| pandas          | 2.2.1      |
| PostgreSQL      | 15         |
| Kafka (Bitnami) | 3.5.1      |
| Zookeeper       | 3.8.1      |
| pgAdmin         | 7          |
| Docker Compose  | 3.8 syntax |

## ✅ Functional Requirements

### ✍️ Phase 1: Setup

All Python containers must install packages from a **shared** `requirements.txt` file located in the project root. Do not split requirements by folder. This enforces consistent environments across all containers and supports automated grading.

- Build Docker images for:
  - `producer`
  - `stream-processor`
  - `batch-ingestor`
  - `scheduler`
  - **Kafka** (Bitnami image)
  - **Zookeeper**
  - **PostgreSQL**
  - **pgAdmin**
- Use `python:3.11.8-slim` as the base image for custom services
- Install all dependencies from `requirements.txt`

### ⚖️ Phase 2: Orchestration

- Use Docker Compose to define all 8 services
- Configure volume mounts:
  - `./configs:/app/configs`
  - `./scripts:/app/scripts`
  - `./lake:/app/lake` *(shared data lake)*
  - `./db:/docker-entrypoint-initdb.d` *(to load schema on Postgres init)*
- Ensure service dependencies:
  - Kafka depends on Zookeeper
  - All others depend on Kafka or Postgres as needed

### 📆 Phase 3: Execution

- Run the following scripts from containers:
  - `generate_people_csv.py`
  - `generate_staff.py`
  - `generate_staff_schedules.py`
  - `assign_illnesses.py`
  - `generate_patient_admissions.py`
  - `generate_patient_transfers.py`
  - `generate_emergency_transport.py`
  - `generate_hospital_summary.py`
- Ensure the PostgreSQL container loads the schema from `db_schema.sql`
- Run `batch_ingestor.py` inside its container to populate PostgreSQL from batch files

## 💼 Deliverables

You are expected to produce:

- A working `docker-compose.yml`
- One `Dockerfile` per custom container (at minimum: producer, scheduler, processor, ingestor)
- Functioning volume mounts to `lake/`
- Generated files in `/lake/batch/` and `/lake/stream/`
- PostgreSQL tables populated from batch data
- Kafka logs proving stream event flow

## ❗ Do NOT

- Run any scripts outside of Docker
- Hardcode paths like `/lake/batch/` in your scripts — these must be dynamic via `simulation_config.py`
- Submit or depend on the `lake/` or `pg_data/` folders — they should be created by containers

## 💡 Tips

- Use a **generic** Dockerfile template for all custom services. It should:

  - Use a lightweight Python base image
  - Copy and install from the shared `requirements.txt`
  - Include only the necessary scripts and configs

- Your Dockerfile might look like:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./<script>.py .
CMD ["python", "<script>.py"]
```

- Your docker-compose service definition should:

  - Use `build: ./<folder>` to point to each custom Dockerfile
  - Include appropriate volume mounts like `./configs:/app/configs`
  - Use `depends_on:` to enforce startup order

- Avoid copying this structure verbatim — build up your files from your understanding of the components.

- Use environment variables and `os.getenv` in scripts for all paths.

- Use `depends_on` to ensure services start in the right order.

- Mount `lake` as a shared volume so all containers can access data.

- Use `logging` inside your scripts for debug output.

## 🫱 Good Luck

This project simulates a production data architecture. Focus on container interaction, volumes, networking, and orchestration. Good luck!

---

*This file is auto-generated for student distribution. Do not modify unless customizing assessment criteria.*

