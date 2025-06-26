# 🏥 Hospital Data Warehouse & Simulation Project

## 📘 Project Overview

This project simulates a digital hospital environment and generates a rich, time-series dataset representing the inner workings of a healthcare system. The pipeline is fully containerized and supports:

- **Synthetic population generation** with comprehensive demographic and medical details.
- **Hospital workforce simulation**, including hiring, retirement, and rotating shift schedules.
- **Daily modeling of patient visits, admissions, and inter-hospital transfers.**
- **Real-time event streaming** (e.g., emergency transports, patient transfers) using Apache Kafka.
- **Batch data ingestion** (e.g., admissions) into a PostgreSQL data warehouse for downstream analysis.

All services run within Docker containers managed via Docker Compose.

---

## 🏗️ Architecture & Data Flow

This system follows a **microservices architecture**, with each container responsible for a specific task. The simulation unfolds in phases:

### 🔧 Initial Setup (via `scheduler`)
Executed once at the start of the simulation to create foundational datasets:

- `people_data.csv`: Full synthetic population.
- `staff_data.csv` & `reserve_pool.csv`: Active workforce and reserve candidates.
- `population_with_illnesses.csv`: People enriched with illness profiles.
- Quarterly files (`staff_active_...`) and monthly schedules (`schedules_...`) for the full simulation.

All outputs are stored in the `shared_data/batch/` directory.

---

### 📅 Daily Simulation Loop (Driven by `scheduler`)
Executed every simulated day:

1. **Generate Patients**
   - `generate_patients.py` creates daily patient visits (`daily_visitors_...csv`).

2. **Simulate Real-Time Events**
   - `generate_emergency_transport.py` and `generate_patient_transfers.py` simulate emergency and transfer events.

---

### 🔄 Real-Time Streaming (Producer & Kafka)
- Streaming scripts send individual event messages to Kafka topics.
- `stream_processor` consumes these messages and stores them as `.json` files in `shared_data/stream/`.

---

### 📦 Batch Processing (Scheduler & Batch Ingestor)
- `generate_patient_admissions.py` creates `admissions_...csv`.
- `batch_ingestor` detects and ingests this file from `shared_data/batch/`.

---

### 🗄️ Data Warehousing (Batch Ingestor → PostgreSQL)
- Batch files are transformed and loaded into a **normalized relational schema** inside the `postgresDB` database.
- After ingestion, files are moved to `shared_data/processed/`.

---

## 📂 Project Structure

