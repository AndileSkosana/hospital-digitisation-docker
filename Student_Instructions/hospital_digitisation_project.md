<span><div class="savanna-styles">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/Explore-AI/Public-Data@master/de-alx/styles.css">

<img
  src="https://raw.githubusercontent.com/Explore-AI/Pictures/master/alx-courses/aice/assets/Content_page_banner_blue_dots.png"
  alt="ALX Content Header"
  class="full-width-image"
/>

<h1> Hospital Digitization Project</h1>
<h2>📘 Overview</h2>

<p>Welcome to your first project as a data engineer – congratulations on reaching this milestone ⭐️!</p>

<p>You’ve just joined a consulting firm that’s been awarded a contract to digitize and consolidate hospital records for a major public hospital. Your role is critical to this transformation. You’ll be working on streaming and batch ingestion of hospital records and helping update a modern data warehouse.</p>

<img src="https://github.com/Explore-AI/Pictures/raw/master/alx-courses/de/DE_Project_pics/Hospital_Office.jpg" alt="A skyscraper with a bright light">

<p>This project will call on your real-world data engineering scenarios involving data ingestion, data cleaning, and real-time database updates using Docker, PostgreSQL, and Kafka.</p>

<p>Your team lead wants to assess your technical abilities with this challenge over the next <strong>5 days</strong>. Your goal is to containerize and orchestrate this system using Docker Compose. You’ve got this! 💪</p>

<h2>🧑‍⚕️ Project Objectives</h2>
<ul>
  <li>Build containers for all components</li>
  <li>Configure Kafka and PostgreSQL services</li>
  <li>Mount shared volumes for data exchange</li>
  <li>Execute Python scripts inside containers</li>
  <li>Persist batch and stream data in a shared lake</li>
</ul>

<h2>📊 Infrastructure Architecture</h2>

<p>You will create **8 services** using Docker:</p>

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

<h2>🗃️ Provided Files</h2>

<p>You have been given:</p>
<pre><code>
/configs/                  # Kafka, DB, and hospital shift configuration
/scripts/                  # Python files for data generation and ingestion
/db/                       # PostgreSQL schema setup files
  └── db_schema.sql        # SQL schema to initialize the hospital database
/requirements.txt          # Required Python packages (for all services)
</code></pre>

> 
<div class="callout">
    <div class="callout-content"> 
        <h>What must you do with the given files?</h><br>
        You must create Dockerfiles for each container and orchestrate them with Docker Compose. Using the given files ensure that the project is able to use the data from these files to ensure the hospital is operational.
    </div>
</div>

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

<h2>✅ Functional Requirements</h2>

<h3>✍️ Stage 1: Project Setup & Configuration</h3>

<p>You’ll need to create the project structure. </p>
<ul>
    <li><strong>Create Your Folders</strong>: Create a main project directory (e.g., `hospital_data_warehouse`). Inside it, create:
        <ul>
            <li> <code>producer</code>: Publishes hospital activity to Kafka topics.
            <li> <code>stream_processor</code>: Consumes Kafka messages and writes to shared stream volume. </li>
            <li> <code>batch_ingestor</code>: Reads CSV files from shared volume and ingests into Postgres.</li>
            <li> <code>scheduler</code>: Runs scripts on a schedule using simulation logic.</li>
            <li> A shared data layer which acts as a data lake where your <code>.daily_flags</code>, <code>.setup_flags</code>, <code>batch</code>, <code>processed</code>, <code>stream</code> and <code>json</code> files will be stored.</li>
            <li> <code>scripts</code>: Folder housing all data generation scripts used within the project.</li>
            <li> <code>configs</code>: Folder where all configs for the project are stored and read from.</li>
        </ul>
    </li>
    <li><strong>Place your scripts in the correct folders</strong>: Move the provided Python scripts into the <code>scripts/</code> folder and <code>config</code> files into the <code>configs/</code> folder.</li>
    <li><strong>💡Review the Configuration:</strong>
        <ul>
            <li>Open <code>database_config.json</code> and consider: What hostname should a container use to find the database within a Docker network?</li>
            <li>Open <code>kafka_config.json</code> and think: How should the producer locate Kafka?</li>
        </ul>
    </li>
    <li>You can generate a text file of your project's folder structure using a simple, universal command-line tool. The best tool for this is <code>tree</code>.
        <ul>
            <li><strong>For Windows users</strong>: From your terminal window you can run a single command from your project's root directory. This command will scan the folder structure and save it to a file named <code>tree.txt</code>. 
            <pre><code>tree /f /a > tree.txt</code></pre></li>
            <li><strong>For macOS / Linux Users</strong>: First, ensure tree is installed. If it's not, it can be installed with <code>brew install tree</code> <strong>(macOS) </strong>or sudo apt-get install tree</code> (Debian/Ubuntu). Then, run this command in the project's root folder 
            <pre><code>tree -a -I '__pycache__|.git|results' > tree.txt</code></pre></li>
        </ul>
    </li>
    <li><strong>Success Criteria</strong>: 
        <ul>
            <li>✅ Folder structure is correct and complete</li>
            <li>✅ Configuration files point to Docker container hostnames</li>
            <li>✅ All infrastructure services defined for orchestration</li>
            <li>⚡ The tree file is the first artifact that can be submitted for auto assessment. You can submit this as many times as you need to get the full marks for this.</li>
        </ul>
    </li>
</ul>
---

<h3>🧱 Stage 2: Dockerizing Your Services</h3>

<p>Each service needs its own <code>Dockerfile</code>. These files define how each container image is built.</p>
<ul>
    <li><strong>💡 Key Concepts:</strong> You will need to structure your dockerfile according to the specific image that you are building for. This is important as this not a one size fits all as different images do different things. The layout of a Dockerfile has the following basic components.
        <ul>
            <li><code>FROM</code>: Base image (e.g., <code>python:3.11-slim</code>)</li>
            <li><code>WORKDIR</code>: Working directory inside the container</li>
            <li><code>COPY</code>: Copy local files into the container</li>
            <li><code>RUN</code>: Run commands during image build (e.g., <code>pip install</code>)</li>
            <li><code>CMD</code>: Command run when the container starts</li>
        </ul>
    </li>
    <li><strong>Create Dockerfiles</strong>: One in each service folder (<code>producer/</code>, <code>scheduler/</code>, <code>scheduler</code>,<code>stream_processor</code>,<code>batch_ingestor</code>).</li>
    <li>Build Instructions:
        <ul>
            <li>Use a Python base image</li>
            <li>Set <code>/app</code> as the working directory</li>
            <li>Copy needed files. Hint: Think about how <code>COPY</code> interacts with build context.</li>
            <li>Install requirements from <code>requirements.txt</code>.</li>
            <li>Set <code>CMD</code> for the main script (e.g., <code>CMD ["python", "scheduler.py"]</code>)</li>
        </ul>
    </li>
    <li>💡<strong>Hint</strong>: Which services run continuously? Which are task runners?</li>
</ul>

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY ../../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./<script>.py .
CMD ["python", "<script>.py"]
```
<em>This is an example of the contents of a simple dockerfile.</em>

<strong>Success Criteria</strong>: 
    <ul>
        <li>✅ Dockerfiles built correctly without errors.</li>
        <li>✅ Dockerfiles follow clean structure and best practices.</li>
        <li>✅ All dependencies installed from a <code>requirements.txt</code> file.</li>
        <li>⚡ The Dockerfile is the next artifact that can be sumitted for auto assessment. You can submit this as many times as you need to get the full marks for this.</li>
    </ul>    
---

<h3> 🔁 Stage 3: Orchestrate with Docker Compose</h3>
<p>Use Docker Compose to define and orchestrate all services. The <code>docker-compose.yml</code> file defines all 8 services and their relationships.</p>
<ul>
    <li> Configure environment variables appropriately</li>
    <li> Volume mounts to enable shared access to configs and generated data</li>
    <li> Compose syntax version: <strong>3.8</strong></li>
    <li>Use official images for <code>zookeeper</code>, <code>kafka</code>, <code>postgres</code>, and <code>pgadmin</code></li>
    <li> Use <code>depends_on</code> to ensure service startup order</li>
</ul>

<strong>Success Criteria</strong>: 
<ul>
    <li>✅ All services defined and run as expected</li>
    <li>✅ Containers start in the correct order</li>
    <li>✅ Services communicate over the same network\ </li>
    <li>✅ Network configuration allows all containers to communicate</li>
    <li>⚡ The <code>docker-compose.yml</code> is the next artifact that can be sumitted for auto assessment. You can submit this as many times as you need to get the full marks for this.</li>
</ul>
---

<h3> 🛠️ Stage 4: Run the pipeline</h3>

<p>This is where the real hands-on learning happens. Expect errors — debugging is part of the process. Once the environment is setup:</p>
<ul>
    <li><strong>Start the pipeline</strong> using the below command:
        <pre><code>docker-compose up --build</code></pre>
    </li>
    <li>Verify the output:
        <ul>
            <li><strong>People and staff data processed</strong>: Generate people and staff data flags created?<li>
            <li> Batch files written to a shared batch folder?</li>
            <li> Stream events written into a shared stream folder?</li>
            <li> Processed files in a processed folder?</li>
            <li> Ingest batch data into PostgreSQL. Ensure the PostgreSQL container loads the schema from `db_schema.sql`</li>
            <li> Kafka logs should show stream events in motion</li>
            <li>💡 depending on the service you are looking at you might want to view the logs using <code>docker-compose logs -f {{name_of_the_service}}</code> e.g <code> docker-compose logs -f scheduler</code> to view the scheduler service.</li>
        </ul>
    </li>
    <li> Some of the common errors you could expect are:
        <ul>
            <li>Incorrect <code>COPY</code> paths</li>
            <li><code>ModuleNotFoundError</code></li>
            <li><code>ForeignKeyViolation</code></li>
            <li>Silent container exits</li>
        </ul>
    </li>
    <li><strong>Read</strong> the logs. <strong>Understand</strong> what the error is. Use AI to help you debug what could be going wrong. <strong>Fix</strong> the problem. <strong>Retry</strong> running the pipeline with the fixes in place.</li>
</ul>
<strong>Success Criteria</strong>: 
<ul>
    <li>✅ Pipeline runs without crashing</li>
    <li>✅ Batch and stream files appear in correct directories</li>
    <li>✅ Events visible in Kafka</li>
    <li>✅ Data ingested into PostgreSQL tables</li>
    <li>⚡ The <code>.flag</code> files in the <code>.setup_flags</code> folder are the next artifacts that can be sumitted for auto assessment. You can submit this as many times as you need to get the full marks for this.</li>
</ul>
---

<h3>🧱 Stage 5: Project Run Verification</h3>

<p>The project will run from the date 20 November 2022 till 31 March 2025 covering 862 days of historical hopsital data. You’ll have to assess the following components:</p>
<ul>
    <li> <strong>Check the Data Lake</strong>:
        <ul>
            <li>Are <code>batch/</code>, <code>stream/</code>, and <code>processed/</code> folders created under a shared folder?</li>
            <li>Do they contain <code>.csv</code>, <code>.json</code> and <code>.txt</code> files?</li>
        </ul>
    </li>
    <li> <strong>Check the Data Warehouse</strong>: 
        <ul>
            <li>Visit [http://localhost:5050](http://localhost:5050)</li>
            <li>Log in to <code>pgAdmin</code></li>
            <li>Connect to <code>postgresDB</code></li>
            <li>Check <code>hospital_db</code> for schemas like <code>hospital_operations</code>, <code>hospital_admissions</code>. You can also run a couple queries to confirm if there is any data in the tables.</li>
        </ul>
    </li>
    <li> The project creates json files for the state it is on. The  
        <code>scheduler_state.json</code> on the final day will reflect:
        <pre><code> 
        {
          "current_sim_date": "2025-03-31"
        }
        </code></pre>                
    </li>
</ul>

<strong>Success Criteria</strong>: 
<ul>
    <li>✅ Dockerfiles built correctly\</li>
    <li>✅ Services communicate over the same network\ </li>
    <li>✅ All dependencies installed from `requirements.txt`</li>
    <li>⚡ The <code>scheduler_state.json</code> files in the shared folder is the next artifact that can be sumitted for auto assessment. You can submit this as many times as you need to get the full marks for this.</li>
</ul>
---

<h2> 🧪 What You’re Being Assessed On</h2>
<ul>
    <li> Correct use of Docker and Compose</li>
    <li> Networking between services (Kafka/Postgres)</li>
    <li> Shared volume usage</li>
    <li> Stream and batch separation</li>
    <li> Config-driven, containerized architecture</li>
</ul>
---
<h2> 📦 What To Submit</h2>

Your auto assessment ZIP file should include:
<ul>
    <li><code>producer/Dockerfile</code> - Uses the correct build context, installs dependencies, and runs the right script</li>
    <li><code>scheduler/Dockerfile</code> - Includes cron installation, setup flags, and scheduled execution logic</li>
    <li><code>batch_ingestor/Dockerfile</code> -	Structured properly with required dependencies</li>
    <li><code>stream_processor/Dockerfile</code> - Structured properly with required dependencies</li>
    <li><code>docker-compose.yml</code> - Correct use of build, depends_on, volumes (including shared_data), and network configuration</li>
    <li><code>simulation_configs.py</code> - Central path config: includes shared data volume path and all key file paths</li>
    <li><code>.setup_flags/</code> folder - Should contain 4 flag files created after each respective setup step</li>
    <li><code>scheduler_state.json</code> - Must contain "current_sim_date": "2025-03-31"</li>
    <li><code>tree.txt</code> - A tree-style folder listing saved in a .txt file</li>
    <li><code>README.md</code> - Includes a short project description, setup steps, and any assumptions</li>
</ul>
---

<h2> 🧭 Constraints</h2>
<ul>
    <li> Only use Docker, Python, Kafka, PostgreSQL</li>
    <li> Do <strong>not</strong> run scripts outside Docker</li>
    <li> All volumes must be container-mounted (no host writes) — these must be dynamic via `simulation_config.py`</li>
    <li> Do not hardcode paths — use environment variables they should be created by containers</li>
</ul>

<img src="https://github.com/Explore-AI/Pictures/raw/master/alx-courses/de/DE_Project_pics/Open_Heart_Hospital.jpg" alt="A hospital with a gloomy feel">

<h2>💡 Tips</h2>

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

<h2> 🧠 Reminder</h2>
<p>This is a real-world production-style data architecture. Focus on container interaction, volumes, networking, and orchestration.</p>

<p>You’re expected to use your problem-solving and system-design skills to complete this over the coming days, digitizing <strong>862 hospital days</strong> of data.</p>

<h2>🫱 Good Luck</h2>
<p>Good luck — and keep your containers healthy! 🐳💊</p>
<img src="https://github.com/Explore-AI/Pictures/raw/master/alx-courses/de/DE_Project_pics/Under_Construction_Hospital.jpg" alt="A hospital under construction">
---

*This file is auto-generated for student distribution. Do not modify unless customizing assessment criteria.*

</div></span>