# 📑 Project Brief: Hospital Digitisation – Containerised Solution

## 🏥 Background

You've joined a digital transformation team at a national health department tasked with simulating and modernizing hospital operations using cloud-native tooling. Your role? To build a containerised data ingestion pipeline that simulates how hospitals could manage patient and staff records in real-time.

## 🎯 Goal

You are required to containerize and orchestrate a multi-service data simulation architecture using Docker and Docker Compose. The solution will mimic a hospital's operational pipeline for data ingestion, including both batch and stream events using PostgreSQL and Kafka.

---

## 🗂️ Project Stages

### 🧱 Stage 1: Build Docker Containers

You’ll containerize the following components:

- `producer`: Publishes hospital activity to Kafka topics.
- `stream_processor`: Consumes Kafka messages and writes to shared stream volume.
- `batch_ingestor`: Reads CSV files from shared volume and ingests into Postgres.
- `scheduler`: Runs scripts on a schedule using simulation logic.

You will also configure:

- `kafka`, `zookeeper` for messaging
- `postgres`, `pgadmin` for data storage and monitoring

**Success Criteria:** ✅ Dockerfiles built correctly\
✅ Services communicate over the same network\
✅ All dependencies installed from `requirements.txt`

---

### 🔁 Stage 2: Orchestrate with Docker Compose

Use Docker Compose to define and orchestrate all services.

- Volume mounts to enable shared access to configs and generated data
- Compose syntax version: **3.8**
- Use `depends_on` to ensure service startup order

---

### 🛠️ Stage 3: Run & Simulate

Once the environment is up:

- Generate people and staff data
- Simulate batch files written to `/lake/batch`
- Simulate stream events into `/lake/stream`
- Ingest batch data into PostgreSQL
- Kafka logs should show stream events in motion

---

## 🧪 What You’re Being Assessed On

- Correct use of Docker and Compose
- Networking between services (Kafka/Postgres)
- Shared volume usage
- Stream and batch separation
- Config-driven, containerized architecture

---

## 📦 What To Submit

Your final ZIP file should include:

- Dockerfiles for each custom service
- A working `docker-compose.yml`
- All config files in `/configs`
- All Python scripts in `/scripts`
- A `README.md` with your setup explanation
- Any additional `.env` files used

---

## 🧭 Constraints

- Only use Docker + Python (no Airflow or Spark)
- Do **not** run scripts outside Docker
- All volumes must be container-mounted (no host writes)
- Do not hardcode paths — use environment variables

---

## 🧠 Reminder

This is a simulation. It’s not about perfect clinical accuracy but about orchestrating a real-world data engineering pipeline.

You’re expected to use your problem-solving and system-design skills to complete this over **9 real-time days**, simulating **1455 hospital days**.

Good luck — and keep your containers healthy! 🐳💊

---

## 🫱 Good Luck

This project simulates a production data architecture. Focus on container interaction, volumes, networking, and orchestration. Good luck!

---

*This file is auto-generated for student distribution. Do not modify unless customizing assessment criteria.*