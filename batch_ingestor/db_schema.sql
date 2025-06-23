-- Create schemas if they don't exist
CREATE SCHEMA IF NOT EXISTS hospital_operations;
CREATE SCHEMA IF NOT EXISTS hospital_admissions;

-- Dimension Tables
CREATE TABLE IF NOT EXISTS hospital_operations.Departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS hospital_admissions.Patients (
    patient_id VARCHAR(255) PRIMARY KEY,
    first_name VARCHAR(255),
    surname VARCHAR(255),
    birthdate DATE,
    gender VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS hospital_admissions.MedicalConditions (
    condition_id SERIAL PRIMARY KEY,
    condition_name VARCHAR(255) UNIQUE NOT NULL,
    severity_level VARCHAR(50)
);

-- Fact Table
CREATE TABLE IF NOT EXISTS hospital_admissions.Admissions (
    admission_id SERIAL PRIMARY KEY,
    patient_id VARCHAR(255) REFERENCES hospital_admissions.Patients(patient_id),
    condition_id INT REFERENCES hospital_admissions.MedicalConditions(condition_id),
    department_id INT REFERENCES hospital_operations.Departments(department_id),
    admission_date TIMESTAMP NOT NULL,
    discharge_date TIMESTAMP
);
