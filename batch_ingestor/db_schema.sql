-- Create schemas if they don't exist
CREATE SCHEMA IF NOT EXISTS hospital_operations;
CREATE SCHEMA IF NOT EXISTS hospital_admissions;
CREATE SCHEMA IF NOT EXISTS hospital_streams;

-- Dimension Tables
CREATE TABLE IF NOT EXISTS hospital_operations.Departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(255) UNIQUE NOT NULL
);

-- --- FIX: New table for the staff master list ---
CREATE TABLE IF NOT EXISTS hospital_operations.Staff (
    staff_id VARCHAR(36) PRIMARY KEY,
    person_id VARCHAR(36) UNIQUE NOT NULL,
    first_name VARCHAR(255),
    surname VARCHAR(255),
    role VARCHAR(100),
    department VARCHAR(100),
    experience_level VARCHAR(50),
    years_of_service INT
);

-- --- FIX: New table for the daily staff schedules ---
CREATE TABLE IF NOT EXISTS hospital_operations.Schedules (
    schedule_id SERIAL PRIMARY KEY,
    staff_id VARCHAR(36) REFERENCES hospital_operations.Staff(staff_id),
    schedule_date DATE NOT NULL,
    shift_name VARCHAR(100),
    is_work_day BOOLEAN,
    assigned_department VARCHAR(100),
    UNIQUE(staff_id, schedule_date) -- Ensures only one schedule entry per staff per day
);


CREATE TABLE IF NOT EXISTS hospital_admissions.Patients (
    patient_id VARCHAR(36) PRIMARY KEY,
    first_name VARCHAR(255),
    surname VARCHAR(255),
    birthdate DATE,
    gender VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS hospital_admissions.MedicalConditions (
    condition_id SERIAL PRIMARY KEY,
    condition_name VARCHAR(255) UNIQUE NOT NULL
);

-- Fact Table
CREATE TABLE IF NOT EXISTS hospital_admissions.Admissions (
    admission_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(36) REFERENCES hospital_admissions.Patients(patient_id),
    condition_id INT REFERENCES hospital_admissions.MedicalConditions(condition_id),
    department_id INT REFERENCES hospital_operations.Departments(department_id),
    admission_date TIMESTAMP NOT NULL,
    discharge_date TIMESTAMP
);

-- Tables for JSON Stream Data
CREATE TABLE IF NOT EXISTS hospital_streams.Transports (
    event_id SERIAL PRIMARY KEY,
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_data JSONB
);

CREATE TABLE IF NOT EXISTS hospital_streams.Transfers (
    event_id SERIAL PRIMARY KEY,
    event_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_data JSONB
);
