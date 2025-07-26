# auto_mark.py
# Auto-marking script for Hospital Digitisation Student Project

import os
import json
from pathlib import Path
import re
import yaml
from datetime import datetime

# --- Configuration ---

# Updated DOCKERFILE_RULES with more specific checks
DOCKERFILE_RULES = {
    "producer": {
        "base_images": ["python:3.11-slim"],
        "required_lines": [
            "WORKDIR /app",
            "COPY producer/requirements.txt .",
            "RUN pip install --no-cache-dir -r requirements.txt",
            "COPY producer/producer.py"
        ]
    },
    "stream_processor": {
        "base_images": ["python:3.11-slim"],
        "required_lines": [
            "WORKDIR /app",
            "COPY stream_processor/requirements.txt .",
            "RUN pip install --no-cache-dir -r requirements.txt",
            "COPY stream_processor/stream_processor.py .",
            "COPY scripts/simulation_config.py .",
            'CMD ["python", "stream_processor.py"]'
        ]
    },
    "batch_ingestor": {
        "base_images": ["python:3.11-slim"],
        "required_lines": [
            "WORKDIR /app",
            "COPY batch_ingestor/requirements.txt .",
            "RUN pip install --no-cache-dir -r requirements.txt",
            "COPY batch_ingestor/batch_ingestor.py .",
            "COPY batch_ingestor/db_schema.sql .",
            "COPY scripts/simulation_config.py .",
            'CMD ["python", "batch_ingestor.py"]'
        ]
    },
    "scheduler": {
        "base_images": ["python:3.11-slim"],
        "required_lines": [
            "WORKDIR /app",
            "COPY scheduler/requirements.txt .",
            "RUN pip install --no-cache-dir -r requirements.txt",
            "COPY scheduler/scheduler.py .",
            "COPY scripts/simulation_config.py .",
            "COPY scripts/utils.py .",
            "COPY scripts/generate_people.py .",
            "COPY scripts/assign_illnesses.py .",
            "COPY scripts/simulate_workforce.py .",
            "COPY scripts/generate_staff_schedules.py .",
            "COPY scripts/generate_patients.py .",
            "COPY scripts/generate_patient_admissions.py .",
            "COPY scripts/generate_patient_transfers.py .",
            "COPY scripts/generate_emergency_transport.py .",
            "COPY scripts/generate_hospital_summary.py .",
            'CMD ["python", "scheduler.py"]'
        ]
    }
}


# --- Individual Check Functions ---

def check_dockerfile_artifact(path, service):
    """Checks a single Dockerfile against its rules."""
    if not path.exists():
        return 0, f"❌ Missing {service}/Dockerfile"

    rules = DOCKERFILE_RULES[service]
    with open(path) as f:
        content = f.read()

    score = 0
    comments = []
    
    if any(f"FROM {base}" in content for base in rules["base_images"]):
        score += 1
    else:
        comments.append("❌ Incorrect or missing base image")

    for line in rules["required_lines"]:
        if line in content:
            score += 1
        else:
            comments.append(f"❌ Missing line: `{line}`")

    max_score = 1 + len(rules["required_lines"])
    feedback = "All good" if not comments else ", ".join(comments)
    return score, f"Service '{service}' ({score}/{max_score}): {feedback}"


def check_simulation_config(project_path):
    """Checks the simulation_config.py for correct constant definitions."""
    config_file = Path(project_path) / "scripts" / "simulation_config.py"
    if not config_file.exists():
        return 0, "❌ Missing simulation_config.py"

    with open(config_file) as f:
        content = f.read()

    required_constants = {
        "BATCH_INTERVAL_SECONDS": "15 * 60", "STREAM_INTERVAL_SECONDS": "3 * 60",
        "LAKE_PATH": '"lake"', "BATCH_DATA_PATH": '"lake/batch"', "FAILED_PATH": '"lake/failed"',
        "STREAM_DATA_PATH": '"lake/stream"', "PROCESSED_DATA_PATH": '"lake/processed"',
        "SETUP_FLAG_PATH": '".setup_flags"', "PEOPLE_DATA_FILE": '"lake/processed/people.csv"',
        "STAFF_DATA_FILE": '"lake/processed/staff.csv"', "RESERVE_POOL_FILE": '"lake/processed/reserve_pool.csv"',
        "ILLNESSES_FILE": '"lake/processed/illnesses.csv"', "SCHEDULES_PATH": "PROCESSED_DATA_PATH",
        "PEOPLE_GENERATED_FLAG": '".setup_flags/people.done"', "STAFF_GENERATED_FLAG": '".setup_flags/staff.done"',
        "ILLNESSES_ASSIGNED_FLAG": '".setup_flags/illnesses.done"', "WORKFORCE_SIMULATED_FLAG": '".setup_flags/workforce.done"',
        "SCHEDULES_GENERATED_FLAG": '".setup_flags/schedules.done"', "INITIAL_DATA_GENERATED_FLAG": '".setup_flags/initial_data.done"',
        "DAILY_FLAG_PATH": '".daily_flags"', "DAILY_VISITORS_FLAG_TPL": '".daily_flags/visitors_{}.done"',
        "DAILY_ADMISSIONS_FLAG_TPL": '".daily_flags/admissions_{}.done"', "DAILY_TRANSPORT_FLAG_TPL": '".daily_flags/transport_{}.done"',
        "DAILY_TRANSFERS_FLAG_TPL": '".daily_flags/transfers_{}.done"'
    }

    score = 0
    comments = []
    for const, expected_value in required_constants.items():
        match = re.search(rf"^{const}\s*=\s*(.+)$", content, re.MULTILINE)
        if match and match.group(1).strip() == expected_value:
            score += 1
        else:
            comments.append(f"Missing or incorrect: {const}")

    total = len(required_constants)
    scaled_score = int((score / total) * 15)
    
    if scaled_score == 15:
        return scaled_score, f"✅ All constants correctly defined ({scaled_score}/15)"
    else:
        return scaled_score, f"❌ {len(comments)} issues found ({scaled_score}/15)"


def check_docker_compose(file_path):
    """Checks the docker-compose.yml file for required services and configuration."""
    expected_services = {
        "zookeeper": {},
        "kafka": {"depends_on": ["zookeeper"]},
        "postgresDB": {},
        "pgadmin": {"depends_on": ["postgresDB"]},
        "producer": {"build": True, "volumes": True, "depends_on": ["kafka"]},
        "stream_processor": {"build": True, "volumes": True, "depends_on": ["kafka"]},
        "batch_ingestor": {"build": True, "volumes": True, "depends_on": ["postgresDB"]},
        "scheduler": {"build": True, "volumes": True, "depends_on": ["producer", "batch_ingestor"]}
    }
    
    if not Path(file_path).exists():
        return 0, "❌ docker-compose.yml not found"

    try:
        with open(file_path) as f:
            compose = yaml.safe_load(f)
        if not compose or not isinstance(compose.get("services"), dict):
            return 0, "❌ docker-compose.yml is invalid or empty"
    except yaml.YAMLError as e:
        return 0, f"❌ Failed to parse docker-compose.yml. Error: {e}"

    score = 0
    feedback = []
    services = compose.get("services", {})
    
    for name, checks in expected_services.items():
        if name not in services:
            feedback.append(f"Missing service: {name}")
            continue

        service_def = services[name]
        if checks.get("build"):
            if service_def.get("build"): score += 1 
            else: feedback.append(f"{name} missing build")
        if checks.get("volumes"):
            if service_def.get("volumes"): score += 1
            else: feedback.append(f"{name} missing volumes")
        if "depends_on" in checks:
            actual_deps = service_def.get("depends_on", [])
            for dep in checks["depends_on"]:
                if dep in actual_deps: score += 1
                else: feedback.append(f"{name} missing dependency on {dep}")
    
    actual_max_score = 15
    scaled_score = int((score / actual_max_score) * 15) if actual_max_score > 0 else 0
    summary = "All good" if not feedback else ", ".join(feedback)
    return scaled_score, f"Score ({scaled_score}/15): {summary}"

def check_flags_and_state(project_path):
    """Checks for setup flags and the final scheduler state."""
    flags_dir = Path(project_path) / ".setup_flags"
    state_file = Path(project_path) / "scheduler_state.json"

    flags_ok = flags_dir.exists() and any(flags_dir.iterdir())
    state_ok = state_file.exists()

    flags_score = 5 if flags_ok else 0
    state_score = 0
    sim_date = "NOT FOUND"

    if state_ok:
        try:
            with open(state_file) as f:
                state_data = json.load(f)
                sim_date = state_data.get("current_sim_date", "MISSING KEY")
                if sim_date == "2025-03-31":
                    state_score = 5
        except Exception as e:
            sim_date = f"ERROR READING FILE: {e}"

    return flags_score, state_score, sim_date

def check_documentation(project_path):
    """Checks for the existence of a README file."""
    readme_file = Path(project_path) / "README.md"
    alt_readme = Path(project_path) / "hospital_digitisation_project.md"
    
    if readme_file.exists() or alt_readme.exists():
        return 10, "✅ README found (10/10)"
    else:
        return 0, "❌ README.md not found (0/10)"

def check_folder_structure(project_path):
    """Checks the folder structure based on a submitted tree.txt file."""
    tree_file = Path(project_path) / "tree.txt"
    if not tree_file.exists():
        return 0, "❌ Missing tree.txt file"
    
    with open(tree_file, 'r') as f:
        content = f.read()

    expected_items = [
        "docker-compose.yml",
        "README.md",
        "batch_ingestor/batch_ingestor.py",
        "batch_ingestor/db_schema.sql",
        "batch_ingestor/Dockerfile",
        "batch_ingestor/requirements.txt",
        "configs/database_config.json",
        "configs/hospital_shift_config.json",
        "configs/kafka_config.json",
        "producer/Dockerfile",
        "producer/producer.py",
        "producer/requirements.txt",
        "scheduler/Dockerfile",
        "scheduler/requirements.txt",
        "scheduler/scheduler.py",
        "scripts/assign_illnesses.py",
        "scripts/generate_emergency_transport.py",
        "scripts/generate_hospital_summary.py",
        "scripts/generate_patients.py",
        "scripts/generate_patient_admissions.py",
        "scripts/generate_patient_transfers.py",
        "scripts/generate_people.py",
        "scripts/generate_staff.py",
        "scripts/generate_staff_schedules.py",
        "scripts/simulate_workforce.py",
        "scripts/simulation_config.py",
        "scripts/utils.py",
        "shared_data/.setup_flags",
        "shared_data/scheduler_state.json"
    ]
    
    score = 0
    missing_items = []
    
    normalized_content = content.replace('\\', '/')
    
    for item in expected_items:
        if item in normalized_content:
            score += 1
        else:
            missing_items.append(item)
    
    max_raw_score = len(expected_items)
    scaled_score = int((score / max_raw_score) * 15) if max_raw_score > 0 else 0
    
    if not missing_items:
        feedback = f"✅ All required files and folders are present ({scaled_score}/15)"
    else:
        feedback = f"❌ Missing {len(missing_items)} items. Score: ({scaled_score}/15). Missing: {', '.join(missing_items)}"
        
    return scaled_score, feedback

def check_service_configs(project_path):
    """Checks database_config.json and kafka_config.json for correct hostnames."""
    db_config_path = Path(project_path) / "configs" / "database_config.json"
    kafka_config_path = Path(project_path) / "configs" / "kafka_config.json"
    
    score = 0
    comments = []
    
    if not db_config_path.exists():
        comments.append("database_config.json not found")
    else:
        try:
            with open(db_config_path) as f:
                db_data = json.load(f)
            if db_data.get("host") == "postgresDB":
                score += 5 # Raw score
            else:
                comments.append("DB host is not 'postgresDB'")
        except Exception:
            comments.append("Could not parse database_config.json")
            
    if not kafka_config_path.exists():
        comments.append("kafka_config.json not found")
    else:
        try:
            with open(kafka_config_path) as f:
                kafka_data = json.load(f)
            servers = kafka_data.get("bootstrap_servers", [])
            if isinstance(servers, list) and "kafka:9092" in servers:
                score += 5 # Raw score
            else:
                comments.append("Kafka bootstrap_servers is not 'kafka:9092'")
        except Exception:
            comments.append("Could not parse kafka_config.json")
    
    scaled_score = int((score / 10) * 15) # Scale raw score (out of 10) to 15
            
    if not comments:
        feedback = f"✅ All service configs are correct ({scaled_score}/15)"
    else:
        feedback = f"❌ Issues found. Score: ({scaled_score}/15). Issues: {', '.join(comments)}"
        
    return scaled_score, feedback

# --- Main Execution ---

def run_all_checks(project_path="."):
    """Runs all checks and prints a consolidated report."""
    project_path = Path(project_path)
    print("--- 🏥 Running Auto-Marking Script ---")

    # 1. Dockerfile Checks (20 marks)
    print("\n## Dockerfile Checks (20 Marks)")
    docker_results = {}
    raw_docker_score = 0
    max_raw_docker_score = sum(1 + len(rules["required_lines"]) for rules in DOCKERFILE_RULES.values())
    
    for service in DOCKERFILE_RULES.keys():
        path = project_path / service / "Dockerfile"
        score, msg = check_dockerfile_artifact(path, service)
        docker_results[service] = msg
        raw_docker_score += score
    
    docker_score = int((raw_docker_score / max_raw_docker_score) * 20) if max_raw_docker_score > 0 else 0
    for msg in docker_results.values():
        print(f"  - {msg}")

    # 2. Simulation Config Check (15 marks)
    print("\n## Simulation Config Check (15 Marks)")
    config_score, config_msg = check_simulation_config(project_path)
    print(f"  - {config_msg}")

    # 3. Service Config Check (15 marks)
    print("\n## Service Config Check (15 Marks)")
    service_score, service_msg = check_service_configs(project_path)
    print(f"  - {service_msg}")

    # 4. Docker Compose Check (15 marks)
    print("\n## Docker Compose Check (15 Marks)")
    compose_score, compose_msg = check_docker_compose(project_path / "docker-compose.yml")
    print(f"  - {compose_msg}")

    # 5. State & Flags Check (10 marks)
    print("\n## Final State & Flags Check (10 Marks)")
    flags_score, state_score, sim_date = check_flags_and_state(project_path)
    print(f"  - Setup Flags: {'✅ Found' if flags_score else '❌ Not found'} ({flags_score}/5)")
    print(f"  - Scheduler State: {'✅ Found' if state_score else '❌ Not found/incorrect'} ({state_score}/5)")
    print(f"    - Final Simulated Date: {sim_date}")

    # 6. Documentation Check (10 marks)
    print("\n## Documentation Check (10 Marks)")
    doc_score, doc_msg = check_documentation(project_path)
    print(f"  - {doc_msg}")
    
    # 7. Folder Structure Check (15 marks)
    print("\n## Folder Structure Check (15 Marks)")
    structure_score, structure_msg = check_folder_structure(project_path)
    print(f"  - {structure_msg}")

    # --- Final Score ---
    total_score = docker_score + config_score + service_score + compose_score + flags_score + state_score + doc_score + structure_score
    print("\n" + "="*40)
    print(f"📊 TOTAL SCORE: {total_score} / 100")
    print("="*40)

    # --- Save Results ---
    save_results(project_path, {
        "total_score": total_score,
        "breakdown": {
            "dockerfiles": {"score": docker_score, "details": docker_results},
            "simulation_config": {"score": config_score, "details": config_msg},
            "service_configs": {"score": service_score, "details": service_msg},
            "docker_compose": {"score": compose_score, "details": compose_msg},
            "state_and_flags": {"score": flags_score + state_score, "details": f"Flags: {flags_score}/5, State: {state_score}/5"},
            "documentation": {"score": doc_score, "details": doc_msg},
            "folder_structure": {"score": structure_score, "details": structure_msg}
        }
    })

def save_results(project_path, results_data):
    """Saves the marking results to .txt and .json files."""
    results_dir = Path(project_path) / "results"
    results_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    json_file = results_dir / f"auto_mark_{timestamp}.json"
    with open(json_file, "w") as f:
        json.dump(results_data, f, indent=2)
    
    print(f"\n📁 Full results saved to: {json_file}")
    print("--- Check Complete ---")

if __name__ == "__main__":
    run_all_checks()