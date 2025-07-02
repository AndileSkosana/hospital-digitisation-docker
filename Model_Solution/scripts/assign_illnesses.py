import pandas as pd
import numpy as np
import json
import random
import logging
import os
import sys
from datetime import datetime

# Import shared utility functions and configuration
from utils import get_age_group, calculate_age
from simulation_config import PEOPLE_DATA_FILE, ILLNESSES_FILE

# --- Configuration & Data Structures ---
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# --- Define possible conditions for special cases ---
CHRONIC_CONDITIONS = ["Diabetes", "Hypertension", "Asthma", "Arthritis", "Heart Disease", "Chronic Kidney Disease"]
PALLIATIVE_CONDITIONS = ["Advanced Cancer", "End-Stage Organ Failure", "Severe Neurological Disease"]
TRANSPLANT_TYPES = ["Kidney Transplant", "Heart Transplant", "Liver Transplant", "Lung Transplant"]
NO_ILLNESS_REPORTED = "No significant illness reported"

# --- Define the age-specific illness probabilities and remedies ---
AGE_SPECIFIC_ISSUE_PROBS = {
    "Chest pain": {
        "0-4": {"probability": 0.0001, "emt_remedies": ["Observation"], "hospital_remedies": ["ECG", "Observation"]},
        "5-14": {"probability": 0.0002, "emt_remedies": ["Observation"], "hospital_remedies": ["ECG", "Observation"]},
        "15-24": {"probability": 0.001, "emt_remedies": ["Observation"], "hospital_remedies": ["ECG", "Blood tests"]},
        "25-44": {"probability": 0.005, "emt_remedies": ["Oxygen", "Observation"], "hospital_remedies": ["ECG", "Blood tests", "Nitrates", "Observation"]},
        "45-64": {"probability": 0.02, "emt_remedies": ["Oxygen", "Aspirin"], "hospital_remedies": ["ECG", "Blood tests", "Oxygen", "Nitrates", "Aspirin"]},
        "65+": {"probability": 0.05, "emt_remedies": ["Oxygen", "Aspirin"], "hospital_remedies": ["ECG", "Blood tests", "Oxygen", "Nitrates", "Aspirin", "Beta-blockers"]},
        "default": {"probability": 0.01, "emt_remedies": ["Observation"], "hospital_remedies": ["Observation", "Further assessment"]}
    },
    "Burns": {
        "0-4": {"probability": 0.02, "emt_remedies": ["Cold water immersion", "Pain management"], "hospital_remedies": ["Cold water immersion", "Burn dressings", "Pain management"]},
        "5-14": {"probability": 0.015, "emt_remedies": ["Cold water immersion", "Pain relief"], "hospital_remedies": ["Cold water immersion", "Pain relief", "Wound dressing"]},
        "15-24": {"probability": 0.008, "emt_remedies": ["Pain relief"], "hospital_remedies": ["Pain relief", "Antibiotic ointment", "Observation"]},
        "25-44": {"probability": 0.006, "emt_remedies": ["Pain relief"], "hospital_remedies": ["Pain relief", "Antibiotic ointment", "Skin graft (severe cases)"]},
        "45-64": {"probability": 0.008, "emt_remedies": ["Pain relief", "Wound care"], "hospital_remedies": ["Pain relief", "Wound care", "Skin graft (severe cases)"]},
        "65+": {"probability": 0.015, "emt_remedies": ["Pain relief", "Wound care"], "hospital_remedies": ["Pain relief", "Wound care", "Hospitalization for severe cases"]},
        "default": {"probability": 0.005, "emt_remedies": ["Assessment", "First aid burn care"], "hospital_remedies": ["Assessment", "First aid burn care"]}
    },
    "Assault-related injuries": {
        "5-14": {"probability": 0.012, "emt_remedies": ["Pain relief", "Wound care"], "hospital_remedies": ["Psychosocial support", "Pain relief", "Wound care"]},
        "15-24": {"probability": 0.025, "emt_remedies": ["Pain relief", "Wound dressing"], "hospital_remedies": ["Pain relief", "Wound dressing", "Trauma counseling"]},
        "25-44": {"probability": 0.018, "emt_remedies": ["Pain management", "Wound care"], "hospital_remedies": ["Pain management", "Imaging for fractures", "Psychosocial support"]},
        "45-64": {"probability": 0.005, "emt_remedies": ["Pain relief", "Wound dressing"], "hospital_remedies": ["Pain relief", "Wound dressing", "Trauma assessment"]},
        "default": {"probability": 0.008, "emt_remedies": ["Assessment", "First aid wound care"], "hospital_remedies": ["Assessment", "First aid wound care", "Psychosocial referral"]}
    },
    "Alcohol-related illness": {
        "15-24": {"probability": 0.02, "emt_remedies": ["Hydration therapy"], "hospital_remedies": ["Hydration therapy", "Electrolyte balance"]},
        "25-44": {"probability": 0.06, "emt_remedies": ["Observation"], "hospital_remedies": ["Liver function tests", "Detoxification management"]},
        "45-64": {"probability": 0.10, "emt_remedies": ["Observation"], "hospital_remedies": ["Liver function tests", "Detoxification", "Psychosocial support"]},
        "65+": {"probability": 0.15, "emt_remedies": ["Observation"], "hospital_remedies": ["Liver function tests", "Medication review", "Complication screening"]},
        "default": {"probability": 0.05, "emt_remedies": ["Observation"], "hospital_remedies": ["Observation", "Referral to a specialist"]}
    },
    "Poisoning": {
        "0-4": {"probability": 0.01, "emt_remedies": ["Activated charcoal"], "hospital_remedies": ["Activated charcoal", "Antidote administration"]},
        "5-14": {"probability": 0.008, "emt_remedies": ["Activated charcoal"], "hospital_remedies": ["Activated charcoal", "Observation"]},
        "15-24": {"probability": 0.006, "emt_remedies": ["Supportive care"], "hospital_remedies": ["Gastrointestinal decontamination", "Supportive care"]},
        "25-44": {"probability": 0.004, "emt_remedies": ["Supportive care"], "hospital_remedies": ["Gastrointestinal decontamination", "Antidote administration", "ICU monitoring"]},
        "45-64": {"probability": 0.003, "emt_remedies": ["Supportive care"], "hospital_remedies": ["Antidote administration", "ICU monitoring", "Psychosocial support"]},
        "65+": {"probability": 0.002, "emt_remedies": ["Supportive care"], "hospital_remedies": ["Antidote administration", "Supportive care", "Neurological assessment"]},
        "default": {"probability": 0.005, "emt_remedies": ["Emergency assessment"], "hospital_remedies": ["Observation", "Emergency assessment"]}
    },
    "Malnutrition": {
        "0-4": {"probability": 0.04, "emt_remedies": ["Nutritional supplements"], "hospital_remedies": ["Nutritional supplements", "Growth monitoring"]},
        "5-14": {"probability": 0.03, "emt_remedies": ["Supportive care"], "hospital_remedies": ["Nutritional therapy", "Supportive care"]},
        "15-24": {"probability": 0.02, "emt_remedies": ["Dietary intervention"], "hospital_remedies": ["Vitamin therapy", "Dietary intervention"]},
        "25-44": {"probability": 0.015, "emt_remedies": ["Lifestyle modifications"], "hospital_remedies": ["Vitamin therapy", "Lifestyle modifications"]},
        "45-64": {"probability": 0.01, "emt_remedies": ["Assessment"], "hospital_remedies": ["Comprehensive nutritional assessment", "Psychosocial support"]},
        "65+": {"probability": 0.008, "emt_remedies": ["Assessment"], "hospital_remedies": ["Comprehensive nutritional assessment", "Palliative nutritional care"]},
        "default": {"probability": 0.02, "emt_remedies": ["Assessment"], "hospital_remedies": ["Assessment", "Specialist referral"]}
    },
    "Severe shortness of breath or difficulty breathing": {
        "0-4": {"probability": 0.02, "emt_remedies": ["Oxygen", "Bronchodilators"], "hospital_remedies": ["Oxygen", "Bronchodilators"]},
        "5-14": {"probability": 0.01, "emt_remedies": ["Oxygen", "Bronchodilators"], "hospital_remedies": ["Oxygen", "Bronchodilators", "Corticosteroids"]},
        "15-24": {"probability": 0.008, "emt_remedies": ["Oxygen", "Bronchodilators"], "hospital_remedies": ["Oxygen", "Bronchodilators", "Corticosteroids"]},
        "25-44": {"probability": 0.01, "emt_remedies": ["Oxygen", "Bronchodilators"], "hospital_remedies": ["Oxygen", "Bronchodilators", "Corticosteroids"]},
        "45-64": {"probability": 0.015, "emt_remedies": ["Oxygen", "CPAP/BiPAP"], "hospital_remedies": ["Oxygen", "Bronchodilators", "Corticosteroids", "CPAP/BiPAP"]},
        "65+": {"probability": 0.03, "emt_remedies": ["Oxygen", "CPAP/BiPAP"], "hospital_remedies": ["Oxygen", "Bronchodilators", "Corticosteroids", "CPAP/BiPAP"]},
        "default": {"probability": 0.015, "emt_remedies": ["Oxygen", "Assessment"], "hospital_remedies": ["Oxygen", "Assessment"]}
    },
    "Stroke symptoms": {
        "0-4": {"probability": 0.00005, "emt_remedies": ["Neurological assessment"], "hospital_remedies": ["Neurological assessment", "Imaging (CT/MRI)"]},
        "5-14": {"probability": 0.0001, "emt_remedies": ["Neurological assessment"], "hospital_remedies": ["Neurological assessment", "Imaging (CT/MRI)"]},
        "15-24": {"probability": 0.0002, "emt_remedies": ["Neurological assessment"], "hospital_remedies": ["Neurological assessment", "Imaging (CT/MRI)"]},
        "25-44": {"probability": 0.0005, "emt_remedies": ["Neurological assessment"], "hospital_remedies": ["Neurological assessment", "Imaging (CT/MRI)", "Thrombolytics (if eligible)"]},
        "45-64": {"probability": 0.002, "emt_remedies": ["Neurological assessment"], "hospital_remedies": ["Neurological assessment", "Imaging (CT/MRI)", "Thrombolytics (if eligible)", "Antiplatelets"]},
        "65+": {"probability": 0.008, "emt_remedies": ["Neurological assessment"], "hospital_remedies": ["Neurological assessment", "Imaging (CT/MRI)", "Antiplatelets", "Supportive care"]},
        "default": {"probability": 0.001, "emt_remedies": ["Neurological assessment"], "hospital_remedies": ["Neurological assessment", "Imaging"]}
    },
    "Heavy, uncontrollable bleeding": {
        "default": {"probability": 0.005, "emt_remedies": ["Direct pressure", "Wound care"], "hospital_remedies": ["Direct pressure", "Wound care", "Blood transfusion (if needed)"]}
    },
    "Major trauma": {
        "15-24": {"probability": 0.005, "emt_remedies": ["Stabilization", "Pain management"], "hospital_remedies": ["Stabilization", "Imaging", "Pain management", "Surgery (if needed)"]},
        "65+": {"probability": 0.004, "emt_remedies": ["Stabilization", "Pain management"], "hospital_remedies": ["Stabilization", "Imaging", "Pain management", "Surgery (if needed)"]},
        "default": {"probability": 0.003, "emt_remedies": ["Assessment", "Stabilization", "Pain relief"], "hospital_remedies": ["Assessment", "Stabilization", "Pain relief"]}
    },
    "Sudden and severe pain (abdomen, chest, head)": {
        "0-4": {"probability": 0.025, "emt_remedies": ["Pain relief", "Observation"], "hospital_remedies": ["Pain relief", "Observation", "Imaging/Tests"]},
        "5-14": {"probability": 0.03, "emt_remedies": ["Pain relief", "Observation"], "hospital_remedies": ["Pain relief", "Observation", "Imaging/Tests"]},
        "default": {"probability": 0.02, "emt_remedies": ["Pain relief"], "hospital_remedies": ["Pain relief", "Diagnostic tests"]}
    },
    "Seizures": {
        "0-4": {"probability": 0.008, "emt_remedies": ["Observation"], "hospital_remedies": ["Observation", "Anticonvulsants (if ongoing)"]},
        "65+": {"probability": 0.006, "emt_remedies": ["Observation"], "hospital_remedies": ["Observation", "Anticonvulsants", "Neurological assessment"]},
        "default": {"probability": 0.004, "emt_remedies": ["Observation"], "hospital_remedies": ["Observation", "Anticonvulsants (if recurrent)"]}
    },
    "Loss of consciousness or fainting": {
        "15-24": {"probability": 0.012, "emt_remedies": ["Observation"], "hospital_remedies": ["Observation", "ECG (if indicated)"]},
        "65+": {"probability": 0.01, "emt_remedies": ["Observation"], "hospital_remedies": ["Observation", "ECG", "Blood tests"]},
        "default": {"probability": 0.008, "emt_remedies": ["Assessment", "Observation"], "hospital_remedies": ["Assessment", "Observation"]}
    },
    "Severe allergic reactions (anaphylaxis)": {
        "0-4": {"probability": 0.0015, "emt_remedies": ["Epinephrine", "Oxygen"], "hospital_remedies": ["Epinephrine", "Antihistamines", "Corticosteroids", "Oxygen"]},
        "5-14": {"probability": 0.0012, "emt_remedies": ["Epinephrine", "Oxygen"], "hospital_remedies": ["Epinephrine", "Antihistamines", "Corticosteroids", "Oxygen"]},
        "default": {"probability": 0.001, "emt_remedies": ["Epinephrine", "Oxygen"], "hospital_remedies": ["Epinephrine", "Antihistamines", "Corticosteroids", "Oxygen"]}
    },
    "High fever": {
        "0-4": {"probability": 0.10, "emt_remedies": ["Antipyretics", "Fluids"], "hospital_remedies": ["Antipyretics", "Fluids", "Observation"]},
        "5-14": {"probability": 0.06, "emt_remedies": ["Antipyretics", "Fluids"], "hospital_remedies": ["Antipyretics", "Fluids", "Observation"]},
        "default": {"probability": 0.04, "emt_remedies": ["Antipyretics", "Fluids"], "hospital_remedies": ["Antipyretics", "Fluids", "Rest"]}
    },
    "Sudden confusion or change in mental status": {
        "65+": {"probability": 0.015, "emt_remedies": ["Assessment", "Supportive care"], "hospital_remedies": ["Assessment", "Blood tests", "Urine analysis", "Supportive care"]},
        "default": {"probability": 0.003, "emt_remedies": ["Neurological assessment"], "hospital_remedies": ["Neurological assessment", "Basic investigations"]}
    },
    "Severe headaches": {
        "5-14": {"probability": 0.03, "emt_remedies": ["Pain relievers (Paracetamol)"], "hospital_remedies": ["Pain relievers (NSAIDs, Paracetamol)", "Rest"]},
        "15-24": {"probability": 0.04, "emt_remedies": ["Pain relievers (NSAIDs)"], "hospital_remedies": ["Pain relievers (NSAIDs, Triptans)", "Antiemetics"]},
        "25-44": {"probability": 0.035, "emt_remedies": ["Pain relievers (NSAIDs)"], "hospital_remedies": ["Pain relievers (NSAIDs, Triptans)", "Antiemetics"]},
        "default": {"probability": 0.025, "emt_remedies": ["Pain relievers"], "hospital_remedies": ["Pain relievers", "Observation"]}
    },
    "Broken bones or significant joint injuries": {
        "0-4": {"probability": 0.01, "emt_remedies": ["Immobilization (splint)", "Pain relief"], "hospital_remedies": ["Immobilization (splint/cast)", "Pain relief"]},
        "5-14": {"probability": 0.025, "emt_remedies": ["Immobilization (splint)", "Pain relief"], "hospital_remedies": ["Immobilization (splint/cast)", "Pain relief", "Reduction (if needed)"]},
        "15-24": {"probability": 0.015, "emt_remedies": ["Immobilization", "Pain relief"], "hospital_remedies": ["Immobilization", "Pain relief", "Reduction (if needed)"]},
        "65+": {"probability": 0.02, "emt_remedies": ["Immobilization", "Pain relief"], "hospital_remedies": ["Immobilization", "Pain relief", "Assessment for surgery"]},
        "default": {"probability": 0.01, "emt_remedies": ["Immobilization", "Pain relief"], "hospital_remedies": ["Immobilization", "Pain relief"]}
    },
    "Severe infections": {
        "0-4": {"probability": 0.03, "emt_remedies": ["Supportive care"], "hospital_remedies": ["Antibiotics (if bacterial)", "Antivirals (if viral)", "Supportive care"]},
        "65+": {"probability": 0.04, "emt_remedies": ["Supportive care", "Fluid management"], "hospital_remedies": ["Antibiotics (if bacterial)", "Antivirals (if viral)", "Supportive care", "Fluid management"]},
        "default": {"probability": 0.02, "emt_remedies": ["Supportive care"], "hospital_remedies": ["Antibiotics (if bacterial)", "Supportive care"]}
    },
    "Chronic Condition": {
        "15-24": {"probability": 0.10, "emt_remedies": ["Assessment"], "hospital_remedies": ["Condition-specific assessment", "Management plan"]},
        "25-44": {"probability": 0.20, "emt_remedies": ["Assessment"], "hospital_remedies": ["Condition-specific assessment", "Management plan", "Medication review"]},
        "45-64": {"probability": 0.35, "emt_remedies": ["Assessment"], "hospital_remedies": ["Condition-specific assessment", "Management plan", "Medication review", "Complication screening"]},
        "65+": {"probability": 0.50, "emt_remedies": ["Assessment"], "hospital_remedies": ["Condition-specific assessment", "Management plan", "Medication review", "Complication management"]},
        "default": {"probability": 0.05, "emt_remedies": ["Assessment"], "hospital_remedies": ["Assessment"]}
    },
    "Palliative Care Need": {
        "45-64": {"probability": 0.02, "emt_remedies": ["Pain management"], "hospital_remedies": ["Pain management", "Symptom control", "Psychosocial support"]},
        "65+": {"probability": 0.05, "emt_remedies": ["Pain management", "Symptom control"], "hospital_remedies": ["Pain management", "Symptom control", "Psychosocial support", "End-of-life care planning"]},
        "default": {"probability": 0.005, "emt_remedies": ["Assessment for palliative needs"], "hospital_remedies": ["Assessment for palliative needs"]}
    },
    "Transplant Assessment": {
        "15-24": {"probability": 0.005, "emt_remedies": ["Assessment"], "hospital_remedies": ["Organ function tests", "Eligibility assessment"]},
        "25-44": {"probability": 0.01, "emt_remedies": ["Assessment"], "hospital_remedies": ["Organ function tests", "Eligibility assessment", "Listing consideration"]},
        "45-64": {"probability": 0.008, "emt_remedies": ["Assessment"], "hospital_remedies": ["Organ function tests", "Eligibility re-assessment"]},
        "default": {"probability": 0.001, "emt_remedies": ["Assessment"], "hospital_remedies": ["Assessment"]}
    },
    "Common Cold/Flu": {
        "0-4": {"probability": 0.25, "emt_remedies": ["Fluids", "Antipyretics"], "hospital_remedies": ["Rest", "Fluids", "Nasal saline", "Antipyretics"]},
        "5-14": {"probability": 0.20, "emt_remedies": ["Fluids", "Antipyretics"], "hospital_remedies": ["Rest", "Fluids", "Antipyretics", "Cough suppressants"]},
        "15-24": {"probability": 0.15, "emt_remedies": ["Rest", "Fluids"], "hospital_remedies": ["Rest", "Fluids", "Symptomatic relief"]},
        "25-44": {"probability": 0.12, "emt_remedies": ["Rest", "Fluids"], "hospital_remedies": ["Rest", "Fluids", "Symptomatic relief"]},
        "45-64": {"probability": 0.10, "emt_remedies": ["Rest", "Fluids"], "hospital_remedies": ["Rest", "Fluids", "Symptomatic relief", "Flu vaccine (prevention)"]},
        "65+": {"probability": 0.18, "emt_remedies": ["Fluids", "Monitoring"], "hospital_remedies": ["Rest", "Fluids", "Antivirals (if applicable)", "Flu vaccine (prevention)", "Monitoring for complications"]},
        "default": {"probability": 0.15, "emt_remedies": ["Symptomatic relief"], "hospital_remedies": ["Symptomatic relief", "Observation"]}
    },
    "Diabetes": {
        "0-4": {"probability": 0.0001, "emt_remedies": ["Observation"], "hospital_remedies": ["Insulin therapy", "Blood glucose monitoring"]},
        "5-14": {"probability": 0.0005, "emt_remedies": ["Observation"], "hospital_remedies": ["Insulin therapy", "Dietary management", "Blood glucose monitoring"]},
        "15-24": {"probability": 0.002, "emt_remedies": ["Observation"], "hospital_remedies": ["Insulin/Oral medications", "Lifestyle modifications", "Regular monitoring"]},
        "25-44": {"probability": 0.015, "emt_remedies": ["Observation"], "hospital_remedies": ["Oral medications", "Dietary control", "Exercise", "Regular monitoring"]},
        "45-64": {"probability": 0.08, "emt_remedies": ["Observation"], "hospital_remedies": ["Medication management", "Dietary control", "Exercise", "Complication screening"]},
        "65+": {"probability": 0.15, "emt_remedies": ["Observation"], "hospital_remedies": ["Medication management", "Dietary control", "Exercise", "Aggressive complication management"]},
        "default": {"probability": 0.03, "emt_remedies": ["Assessment"], "hospital_remedies": ["Assessment", "Lifestyle advice"]}
    },
    "Hypertension (High Blood Pressure)": {
        "0-14": {"probability": 0.0001, "emt_remedies": ["Monitoring"], "hospital_remedies": ["Lifestyle changes", "Medication (if severe)"]},
        "15-24": {"probability": 0.005, "emt_remedies": ["Monitoring"], "hospital_remedies": ["Lifestyle changes", "Monitoring"]},
        "25-44": {"probability": 0.05, "emt_remedies": ["Lifestyle modifications"], "hospital_remedies": ["Lifestyle modifications (diet, exercise)", "Medication (if needed)"]},
        "45-64": {"probability": 0.20, "emt_remedies": ["Monitoring"], "hospital_remedies": ["Medication (Antihypertensives)", "Dietary changes (low sodium)", "Regular exercise", "Monitoring"]},
        "65+": {"probability": 0.45, "emt_remedies": ["Monitoring"], "hospital_remedies": ["Medication management", "Lifestyle modifications", "Regular monitoring for complications (heart, kidney, stroke)"]},
        "default": {"probability": 0.02, "emt_remedies": ["Blood pressure measurement"], "hospital_remedies": ["Blood pressure measurement", "Lifestyle advice"]}
    },
    "Asthma": {
        "0-4": {"probability": 0.05, "emt_remedies": ["Bronchodilators (inhalers)", "Oxygen"], "hospital_remedies": ["Bronchodilators (inhalers)", "Corticosteroids (if persistent)", "Trigger avoidance"]},
        "5-14": {"probability": 0.085, "emt_remedies": ["Bronchodilators (inhalers)", "Oxygen"], "hospital_remedies": ["Inhaled corticosteroids", "Bronchodilators", "Asthma action plan", "Trigger avoidance"]},
        "15-24": {"probability": 0.06, "emt_remedies": ["Inhaler management"], "hospital_remedies": ["Inhaler management", "Trigger avoidance", "Symptom monitoring"]},
        "25-44": {"probability": 0.04, "emt_remedies": ["Inhaler management"], "hospital_remedies": ["Inhaler management", "Trigger avoidance", "Regular check-ups"]},
        "45-64": {"probability": 0.03, "emt_remedies": ["Medication adherence"], "hospital_remedies": ["Medication adherence", "Pulmonary function tests", "Complication prevention"]},
        "65+": {"probability": 0.02, "emt_remedies": ["Optimized medication regimen"], "hospital_remedies": ["Optimized medication regimen", "Monitoring for other respiratory issues", "Vaccinations"]},
        "default": {"probability": 0.04, "emt_remedies": ["Assessment"], "hospital_remedies": ["Assessment", "Inhaler demonstration"]}
    },
    "Gastroenteritis (Stomach Flu)": {
        "0-4": {"probability": 0.15, "emt_remedies": ["Oral rehydration solution (ORS)"], "hospital_remedies": ["Oral rehydration solution (ORS)", "Small, frequent feeds", "Monitoring for dehydration"]},
        "5-14": {"probability": 0.10, "emt_remedies": ["Oral rehydration solution (ORS)"], "hospital_remedies": ["Oral rehydration solution (ORS)", "Bland diet", "Rest"]},
        "15-24": {"probability": 0.05, "emt_remedies": ["Fluids", "Rest"], "hospital_remedies": ["Fluids", "Rest", "Bland diet"]},
        "25-44": {"probability": 0.03, "emt_remedies": ["Fluids", "Rest"], "hospital_remedies": ["Fluids", "Rest", "Symptomatic relief"]},
        "45-64": {"probability": 0.02, "emt_remedies": ["Fluids", "Rest"], "hospital_remedies": ["Fluids", "Rest", "Monitoring for electrolyte imbalance"]},
        "65+": {"probability": 0.03, "emt_remedies": ["Fluids", "Monitoring"], "hospital_remedies": ["Hospitalization for severe dehydration", "Intravenous fluids", "Monitoring"]},
        "default": {"probability": 0.05, "emt_remedies": ["Hydration"], "hospital_remedies": ["Hydration", "Observation"]}
    },
    "Arthritis (Osteoarthritis/Rheumatoid Arthritis)": {
        "0-14": {"probability": 0.0001, "emt_remedies": ["Pain management"], "hospital_remedies": ["Specialist referral", "Physical therapy"]}, # Juvenile forms
        "15-24": {"probability": 0.001, "emt_remedies": ["Pain management"], "hospital_remedies": ["Pain management", "Physical therapy"]},
        "25-44": {"probability": 0.01, "emt_remedies": ["Pain relievers (NSAIDs)"], "hospital_remedies": ["Pain relievers (NSAIDs)", "Physical therapy", "Lifestyle adjustments"]},
        "45-64": {"probability": 0.15, "emt_remedies": ["Pain management (NSAIDs)"], "hospital_remedies": ["Pain management (NSAIDs, topical creams)", "Physical therapy", "Joint injections", "Weight management"]},
        "65+": {"probability": 0.30, "emt_remedies": ["Pain management"], "hospital_remedies": ["Pain management", "Physical therapy", "Joint replacement (if severe)", "Occupational therapy"]},
        "default": {"probability": 0.05, "emt_remedies": ["Pain relief"], "hospital_remedies": ["Assessment", "Pain relief"]}
    },
    "Tuberculosis (TB)": {
        "0-4": {"probability": 0.0005, "emt_remedies": ["Nutritional support"], "hospital_remedies": ["Anti-TB medication", "Nutritional support", "Monitoring for complications"]},
        "5-14": {"probability": 0.001, "emt_remedies": ["Anti-TB medication"], "hospital_remedies": ["Anti-TB medication", "Directly Observed Treatment, Short-course (DOTS)"]},
        "15-24": {"probability": 0.008, "emt_remedies": ["Anti-TB medication"], "hospital_remedies": ["Anti-TB medication", "DOTS", "Contact tracing"]},
        "25-44": {"probability": 0.012, "emt_remedies": ["Anti-TB medication"], "hospital_remedies": ["Anti-TB medication", "DOTS", "Sputum testing", "Monitoring for drug resistance"]},
        "45-64": {"probability": 0.010, "emt_remedies": ["Anti-TB medication"], "hospital_remedies": ["Anti-TB medication", "DOTS", "Monitoring for co-morbidities"]},
        "65+": {"probability": 0.007, "emt_remedies": ["Anti-TB medication"], "hospital_remedies": ["Anti-TB medication", "DOTS", "Management of weakened immune system"]},
        "default": {"probability": 0.005, "emt_remedies": ["Diagnostic testing"], "hospital_remedies": ["Diagnostic testing", "Isolation (if active)", "Referral to TB clinic"]}
    },
    "HIV/AIDS": {
        "0-4": {"probability": 0.0002, "emt_remedies": ["ART"], "hospital_remedies": ["Antiretroviral therapy (ART)", "Prophylaxis for opportunistic infections"]},
        "5-14": {"probability": 0.0005, "emt_remedies": ["ART"], "hospital_remedies": ["ART", "Monitoring CD4 count and viral load"]},
        "15-24": {"probability": 0.015, "emt_remedies": ["ART adherence counseling"], "hospital_remedies": ["ART initiation and adherence counseling", "Opportunistic infection prevention"]},
        "25-44": {"probability": 0.03, "emt_remedies": ["ART adherence"], "hospital_remedies": ["Lifelong ART adherence", "Regular monitoring", "Management of co-infections"]},
        "45-64": {"probability": 0.02, "emt_remedies": ["ART management"], "hospital_remedies": ["ART management", "Monitoring for long-term complications and comorbidities"]},
        "65+": {"probability": 0.01, "emt_remedies": ["ART management"], "hospital_remedies": ["ART management", "Comprehensive geriatric assessment", "Management of age-related and HIV-related conditions"]},
        "default": {"probability": 0.008, "emt_remedies": ["HIV testing"], "hospital_remedies": ["HIV testing", "Counseling", "Referral for ART"]}
    },
    "Obesity Related Complications": {
        "0-4": {"probability": 0.0013, "emt_remedies": ["Nutritional guidance"], "hospital_remedies": ["Nutritional guidance for parents", "Encourage physical activity", "Monitor growth"]},
        "5-14": {"probability": 0.030, "emt_remedies": ["Dietary education"], "hospital_remedies": ["Family-based lifestyle intervention", "Dietary education", "Increased physical activity"]},
        "15-24": {"probability": 0.035, "emt_remedies": ["Dietary counseling"], "hospital_remedies": ["Dietary counseling", "Exercise programs", "Behavioral therapy", "Screening for co-morbidities"]},
        "25-44": {"probability": 0.040, "emt_remedies": ["Lifestyle modifications"], "hospital_remedies": ["Structured weight loss programs", "Dietary modifications", "Increased physical activity", "Medical management of complications (e.g., diabetes, hypertension)"]},
        "45-64": {"probability": 0.055, "emt_remedies": ["Lifestyle intervention"], "hospital_remedies": ["Comprehensive lifestyle intervention", "Pharmacotherapy (if indicated)", "Bariatric surgery evaluation (severe cases)", "Management of metabolic syndrome"]},
        "65+": {"probability": 0.040, "emt_remedies": ["Healthy aging focus"], "hospital_remedies": ["Focus on healthy aging", "Moderate weight management goals", "Physical activity for mobility", "Nutritional support to prevent sarcopenia"]},
        "default": {"probability": 0.025, "emt_remedies": ["BMI assessment"], "hospital_remedies": ["BMI assessment", "Lifestyle counseling", "Referral to dietitian/exercise physiologist"]}
    },
    "Attempted Suicide": {
        "0-4": {"probability": 0.00001, "emt_remedies": ["Immediate medical attention"], "hospital_remedies": ["Immediate medical attention", "Psychiatric assessment", "Family therapy", "Child protection services involvement"]},
        "5-14": {"probability": 0.001, "emt_remedies": ["Emergency medical care"], "hospital_remedies": ["Emergency medical care", "Psychiatric hospitalization/evaluation", "Individual and family therapy", "Safety planning", "School support"]},
        "15-24": {"probability": 0.005, "emt_remedies": ["Emergency medical care", "Crisis intervention"], "hospital_remedies": ["Emergency medical care", "Psychiatric hospitalization/crisis intervention", "Intensive psychotherapy (CBT/DBT)", "Medication management", "Peer support groups", "Lethal means restriction"]},
        "25-44": {"probability": 0.003, "emt_remedies": ["Crisis intervention"], "hospital_remedies": ["Crisis intervention", "Psychiatric evaluation", "Long-term psychotherapy", "Social support enhancement", "Addressing underlying mental health conditions (depression, anxiety, substance abuse)"]},
        "45-64": {"probability": 0.002, "emt_remedies": ["Crisis intervention"], "hospital_remedies": ["Crisis intervention", "Psychiatric assessment", "Addressing life stressors (financial, relationship)", "Geriatric mental health services", "Community support"]},
        "65+": {"probability": 0.001, "emt_remedies": ["Emergency medical stabilization"], "hospital_remedies": ["Emergency medical stabilization", "Comprehensive psychiatric assessment", "Addressing social isolation, chronic pain, grief", "Integration with primary care", "Family support"]},
        "default": {"probability": 0.001, "emt_remedies": ["Crisis stabilization"], "hospital_remedies": ["Crisis stabilization", "Mental health assessment", "Safety planning", "Referral to mental health services (SADAG, LifeLine)"]}
    },
    "Suicide": { # This refers to completed suicide, often for statistical tracking and understanding risk factors
        "0-14": {"probability": 0.000005, "emt_remedies": ["Postvention support"], "hospital_remedies": ["Postvention support for affected individuals and community", "Risk factor identification and prevention strategies"]},
        "15-24": {"probability": 0.0002, "emt_remedies": ["Grief counseling"], "hospital_remedies": ["Grief counseling for families and peers", "Community-wide prevention programs", "Mental health awareness campaigns", "Lethal means reduction"]},
        "25-44": {"probability": 0.00015, "emt_remedies": ["Public health campaigns"], "hospital_remedies": ["Public health campaigns on mental wellness", "Improved access to mental healthcare", "Support for men (higher risk in SA)"]},
        "45-64": {"probability": 0.00018, "emt_remedies": ["Targeted interventions"], "hospital_remedies": ["Targeted interventions for mid-life despair (as seen in SA data)", "Financial and relationship counseling support", "Mental health screening in primary care"]},
        "65+": {"probability": 0.0001, "emt_remedies": ["Geriatric mental health initiatives"], "hospital_remedies": ["Geriatric mental health initiatives", "Addressing loneliness and end-of-life care discussions", "Training healthcare providers on elderly suicide risk"]},
        "default": {"probability": 0.0001, "emt_remedies": ["Crisis hotline promotion"], "hospital_remedies": ["Public health messaging on help-seeking", "Community mental health support", "Crisis hotline promotion"]}
    },
    "Anxiety Disorders": {
        "0-4": {"probability": 0.005, "emt_remedies": ["Parental guidance"], "hospital_remedies": ["Play therapy", "Parental guidance on managing anxiety", "Early intervention"]},
        "5-14": {"probability": 0.003, "emt_remedies": ["Therapy referral"], "hospital_remedies": ["Cognitive Behavioral Therapy (CBT) for children", "Family therapy", "School support", "Medication (if severe)"]},
        "15-24": {"probability": 0.08, "emt_remedies": ["Counseling referral"], "hospital_remedies": ["CBT", "Mindfulness techniques", "Medication (SSRIs)", "Support groups", "Stress management education"]},
        "25-44": {"probability": 0.12, "emt_remedies": ["Counseling referral"], "hospital_remedies": ["Psychotherapy (CBT, exposure therapy)", "Pharmacotherapy (SSRIs, SNRIs)", "Lifestyle modifications (exercise, diet)", "Stress reduction strategies"]},
        "45-64": {"probability": 0.10, "emt_remedies": ["Medication review"], "hospital_remedies": ["CBT", "Medication review (considering polypharmacy)", "Relaxation techniques", "Addressing co-morbid medical conditions"]},
        "65+": {"probability": 0.07, "emt_remedies": ["Social engagement referral"], "hospital_remedies": ["Gentle psychotherapy", "Medication adjustments (lower doses, fewer side effects)", "Social engagement programs", "Addressing health-related anxiety"]},
        "default": {"probability": 0.05, "emt_remedies": ["Mental health screening"], "hospital_remedies": ["Mental health screening", "Psychoeducation", "Referral for specialized therapy"]}
    },
    "Depression": {
        "0-4": {"probability": 0.001, "emt_remedies": ["Caregiver support"], "hospital_remedies": ["Caregiver support", "Early developmental intervention"]},
        "5-14": {"probability": 0.02, "emt_remedies": ["Therapy referral"], "hospital_remedies": ["Child and adolescent psychotherapy", "Family involvement", "School-based support", "Medication (if severe and persistent)"]},
        "15-24": {"probability": 0.10, "emt_remedies": ["Counseling referral"], "hospital_remedies": ["Psychotherapy (CBT, IPT)", "Antidepressant medication", "Peer support", "Lifestyle changes (exercise, sleep, diet)"]},
        "25-44": {"probability": 0.15, "emt_remedies": ["Counseling referral"], "hospital_remedies": ["Psychotherapy", "Antidepressant medication", "Addressing psychosocial stressors (work, relationships, financial)", "Support networks"]},
        "45-64": {"probability": 0.18, "emt_remedies": ["Screening"], "hospital_remedies": ["Psychotherapy", "Antidepressant medication", "Addressing life transitions (menopause, retirement planning)", "Screening for underlying medical causes"]},
        "65+": {"probability": 0.20, "emt_remedies": ["Geriatric screening"], "hospital_remedies": ["Geriatric depression screening", "Psychotherapy (e.g., Problem-Solving Therapy)", "Careful medication management (lower doses, fewer interactions)", "Social support programs"]},
        "default": {"probability": 0.08, "emt_remedies": ["Mental health assessment"], "hospital_remedies": ["Mental health assessment", "Support and counseling", "Referral to psychiatrist/psychologist"]}
    },
    "Substance Use Disorders (non-alcohol)": {
        "0-14": {"probability": 0.005, "emt_remedies": ["Family education"], "hospital_remedies": ["Family-based prevention programs", "Early intervention for experimentation", "Parental education"]},
        "15-24": {"probability": 0.07, "emt_remedies": ["Counseling referral"], "hospital_remedies": ["Adolescent-specific counseling", "Peer support (e.g., Narcotics Anonymous)", "Detoxification (if needed)", "Rehabilitation programs", "Addressing co-occurring mental health issues"]},
        "25-44": {"probability": 0.04, "emt_remedies": ["Addiction counseling referral"], "hospital_remedies": ["Addiction counseling", "Medication-assisted treatment (if applicable)", "Rehabilitation", "Relapse prevention strategies", "Harm reduction approaches"]},
        "45-64": {"probability": 0.02, "emt_remedies": ["Therapy referral"], "hospital_remedies": ["Individual and group therapy", "Pharmacotherapy", "Addressing health complications", "Social reintegration support"]},
        "65+": {"probability": 0.005, "emt_remedies": ["Screening"], "hospital_remedies": ["Screening for substance use in elderly", "Tailored treatment considering age-related health", "Support for social isolation"]},
        "default": {"probability": 0.03, "emt_remedies": ["Screening"], "hospital_remedies": ["Screening for substance use", "Brief intervention", "Referral to addiction services"]}
    },
    "Road Traffic Injuries": {
        "0-4": {"probability": 0.008, "emt_remedies": ["Emergency medical care", "Trauma assessment"], "hospital_remedies": ["Emergency medical care", "Trauma assessment", "Child safety seat promotion", "Pedestrian safety education"]},
        "5-14": {"probability": 0.015, "emt_remedies": ["Emergency medical care", "Trauma care"], "hospital_remedies": ["Emergency medical care", "Trauma care", "Rehabilitation", "Road safety education (pedestrians, cyclists)"]},
        "15-24": {"probability": 0.03, "emt_remedies": ["Emergency trauma care"], "hospital_remedies": ["Emergency trauma care", "Orthopedic surgery", "Rehabilitation", "Driver education (e.g., distracted driving, speed)", "Addressing alcohol/drug impairment"]},
        "25-44": {"probability": 0.02, "emt_remedies": ["Trauma management"], "hospital_remedies": ["Trauma management", "Surgical interventions", "Physical therapy", "Work reintegration support", "Fatigue awareness"]},
        "45-64": {"probability": 0.01, "emt_remedies": ["Injury management"], "hospital_remedies": ["Comprehensive injury management", "Rehabilitation", "Addressing pre-existing health conditions", "Vehicle safety features awareness"]},
        "65+": {"probability": 0.007, "emt_remedies": ["Geriatric trauma protocols"], "hospital_remedies": ["Geriatric trauma protocols", "Fall prevention in vehicles", "Vision and reaction time assessment for drivers", "Pedestrian visibility"]},
        "default": {"probability": 0.015, "emt_remedies": ["Emergency assessment", "Trauma stabilization"], "hospital_remedies": ["Emergency assessment", "Trauma stabilization", "Imaging"]}
    },
    "Domestic Violence Injuries": {
        "0-4": {"probability": 0.001, "emt_remedies": ["Medical assessment", "Child protection services"], "hospital_remedies": ["Child protection services", "Medical assessment for non-accidental trauma", "Support for caregivers", "Safe housing"]},
        "5-14": {"probability": 0.003, "emt_remedies": ["Medical evaluation"], "hospital_remedies": ["Medical evaluation", "Psychological support (trauma counseling)", "Safe environment provision", "School awareness programs"]},
        "15-24": {"probability": 0.015, "emt_remedies": ["Emergency medical care", "Safety planning"], "hospital_remedies": ["Emergency medical care", "Safety planning", "Crisis counseling", "Legal aid referral (protection orders)", "Shelter services"]},
        "25-44": {"probability": 0.02, "emt_remedies": ["Medical treatment"], "hospital_remedies": ["Medical treatment of injuries", "Comprehensive psychosocial support", "Legal and advocacy services", "Support groups", "Addressing long-term health impacts"]},
        "45-64": {"probability": 0.01, "emt_remedies": ["Injury management"], "hospital_remedies": ["Injury management", "Psychological counseling", "Legal assistance", "Financial empowerment support", "Elder abuse prevention"]},
        "65+": {"probability": 0.005, "emt_remedies": ["Screening for elder abuse"], "hospital_remedies": ["Screening for elder abuse", "Medical and social services coordination", "Safety planning", "Legal protection"]},
        "default": {"probability": 0.008, "emt_remedies": ["Immediate safety assessment", "Medical attention"], "hospital_remedies": ["Immediate safety assessment", "Medical attention for injuries", "Confidential counseling and referral services"]}
    },
    "Chronic Kidney Disease (CKD)": {
        "0-14": {"probability": 0.0001, "emt_remedies": ["Dietary management"], "hospital_remedies": ["Pediatric nephrology consultation", "Dietary management", "Growth monitoring", "Management of underlying conditions"]},
        "15-24": {"probability": 0.0005, "emt_remedies": ["Nephrology follow-up"], "hospital_remedies": ["Nephrology follow-up", "Blood pressure control", "Dietary restrictions", "Education on kidney health"]},
        "25-44": {"probability": 0.005, "emt_remedies": ["Monitoring kidney function"], "hospital_remedies": ["Regular monitoring of kidney function", "Blood pressure and diabetes control", "Medication (e.g., ACE inhibitors/ARBs)", "Lifestyle modifications"]},
        "45-64": {"probability": 0.04, "emt_remedies": ["BP/Diabetes control"], "hospital_remedies": ["Aggressive management of hypertension and diabetes", "Dietary protein restriction (if advised)", "Regular GFR monitoring", "Preparation for renal replacement therapy (dialysis/transplant) if progression occurs"]},
        "65+": {"probability": 0.08, "emt_remedies": ["Medication review"], "hospital_remedies": ["Careful medication management", "Fluid and electrolyte balance", "Nutritional support", "Shared decision-making on renal replacement therapy options (dialysis, conservative management)", "Palliative care if advanced"]},
        "default": {"probability": 0.01, "emt_remedies": ["Kidney function tests"], "hospital_remedies": ["Initial kidney function tests (creatinine, eGFR, urine albumin)", "Risk factor assessment", "Referral to nephrologist"]}
    },"Chest pain": {
        "0-4": {"probability": 0.0001, "emt_remedies": ["Observation"], "hospital_remedies": ["ECG", "Observation"]},
        "5-14": {"probability": 0.0002, "emt_remedies": ["Observation"], "hospital_remedies": ["ECG", "Observation"]},
        "15-24": {"probability": 0.001, "emt_remedies": ["Observation"], "hospital_remedies": ["ECG", "Blood tests"]},
        "25-44": {"probability": 0.005, "emt_remedies": ["Oxygen", "Observation"], "hospital_remedies": ["ECG", "Blood tests", "Nitrates", "Observation"]},
        "45-64": {"probability": 0.02, "emt_remedies": ["Oxygen", "Aspirin"], "hospital_remedies": ["ECG", "Blood tests", "Oxygen", "Nitrates", "Aspirin"]},
        "65+": {"probability": 0.05, "emt_remedies": ["Oxygen", "Aspirin"], "hospital_remedies": ["ECG", "Blood tests", "Oxygen", "Nitrates", "Aspirin", "Beta-blockers"]},
        "default": {"probability": 0.01, "emt_remedies": ["Observation"], "hospital_remedies": ["Observation", "Further assessment"]}
    },
    "Pregnancy": {
        "0-4": {"probability": 0.0000001, "emt_remedies": ["N/A"], "hospital_remedies": ["N/A"]}, # Extremely low, for edge cases or data errors (e.g., data input error)
        "5-14": {"probability": 0.0001, "emt_remedies": ["Maternal Monitoring", "Supportive Care"], "hospital_remedies": ["Obstetrics Consultation", "Fetal Monitoring", "Counseling"]}, # Early/rare cases
        "15-24": {"probability": 0.005, "emt_remedies": ["Maternal Monitoring", "Vital Signs Check", "Supportive Care"], "hospital_remedies": ["Obstetrics Consultation", "Fetal Monitoring", "Prenatal Check-up", "Ultrasound"]},
        "25-44": {"probability": 0.01, "emt_remedies": ["Maternal Monitoring", "Vital Signs Check", "Supportive Care", "Pain Management"], "hospital_remedies": ["Obstetrics Consultation", "Fetal Monitoring", "Labor and Delivery Support", "Ultrasound", "Postnatal Care"]},
        "45-64": {"probability": 0.001, "emt_remedies": ["Maternal Monitoring", "Vital Signs Check", "Supportive Care"], "hospital_remedies": ["Obstetrics Consultation", "Fetal Monitoring", "High-Risk Pregnancy Management", "Counseling"]},
        "65+": {"probability": 0.0000001, "emt_remedies": ["N/A"], "hospital_remedies": ["N/A"]}, # Extremely low, for edge cases or data errors
        "default": {"probability": 0.0005, "emt_remedies": ["Supportive Care"], "hospital_remedies": ["General Consultation", "Referral to OB/GYN"]}
    },
    "Gestational Diabetes": {
        "0-4": {"probability": 0.00000001, "emt_remedies": ["N/A"], "hospital_remedies": ["N/A"]}, # Effectively zero, as it's pregnancy-related
        "5-14": {"probability": 0.0000001, "emt_remedies": ["Blood Glucose Check", "Supportive Care"], "hospital_remedies": ["OGTT", "Endocrinology Consult", "Dietary Counseling"]}, # Effectively zero, but with placeholder remedies
        "15-24": {"probability": 0.0008, "emt_remedies": ["Blood Glucose Check", "Hydration", "Basic Life Support if needed"], "hospital_remedies": ["Oral Glucose Tolerance Test (OGTT)", "Dietary Counseling", "Blood Sugar Monitoring", "Obstetrics Consult", "Fetal Monitoring"]},
        "25-44": {"probability": 0.002, "emt_remedies": ["Blood Glucose Check", "Hydration", "Basic Life Support if needed"], "hospital_remedies": ["Oral Glucose Tolerance Test (OGTT)", "Dietary Counseling", "Blood Sugar Monitoring", "Insulin Management", "Obstetrics Consult", "Fetal Monitoring", "Postnatal Glucose Screening"]},
        "45-64": {"probability": 0.0001, "emt_remedies": ["Blood Glucose Check", "Supportive Care"], "hospital_remedies": ["OGTT", "Endocrinology Consult", "Dietary Counseling", "Fetal Monitoring"]}, # Lower probability due to less frequent pregnancies
        "65+": {"probability": 0.00000001, "emt_remedies": ["N/A"], "hospital_remedies": ["N/A"]}, # Effectively zero
        "default": {"probability": 0.0001, "emt_remedies": ["Blood Glucose Check"], "hospital_remedies": ["Glucose Screening", "Referral for Pregnancy Assessment"]}
    },
    "No significant illness reported": {
        "default": {"probability": 0.65, "emt_remedies": ["No specific intervention needed"], "hospital_remedies": ["Routine check-up", "No specific medical intervention needed"]}
    }
}

def assign_illnesses_chunked(people_csv_filepath, output_csv_filepath, chunksize=100000):
    """
    Efficiently assigns illnesses and remedies in chunks to prevent memory issues.
    """
    logging.info(f"Starting illness assignment from '{people_csv_filepath}'")
    
    try:
        chunk_iterator = pd.read_csv(people_csv_filepath, chunksize=chunksize, iterator=True)
    except FileNotFoundError:
        logging.error(f"Input file not found: {people_csv_filepath}")
        return

    is_first_chunk = True
    for chunk in chunk_iterator:
        chunk['Age'] = chunk['Birthdate'].apply(calculate_age)
        chunk['age_group_at_assessment'] = chunk['Age'].apply(get_age_group)
        
        # Initialize list columns correctly
        chunk['assigned_issues'] = [[] for _ in range(len(chunk))]
        chunk['emt_remedies'] = [[] for _ in range(len(chunk))]
        chunk['hospital_remedies'] = [[] for _ in range(len(chunk))]

        # Assign illnesses based on probability
        for issue, age_group_info in AGE_SPECIFIC_ISSUE_PROBS.items():
            probabilities = chunk["age_group_at_assessment"].map(
                lambda ag: age_group_info.get(ag, age_group_info["default"]).get("probability", 0)
            )
            illness_mask = np.random.rand(len(chunk)) < probabilities
            
            for idx in chunk[illness_mask].index:
                # Use .loc to ensure we are modifying the original DataFrame chunk
                chunk.loc[idx, "assigned_issues"].append(issue)
                age_group = chunk.loc[idx, "age_group_at_assessment"]
                remedies = age_group_info.get(age_group, age_group_info["default"])
                chunk.loc[idx, "emt_remedies"].extend(remedies.get("emt_remedies", []))
                chunk.loc[idx, "hospital_remedies"].extend(remedies.get("hospital_remedies", []))

        # Handle special cases and default no-illness assignment
        for idx, row in chunk.iterrows():
            issues = row['assigned_issues']
            if "Chronic Condition" in issues:
                issues.remove("Chronic Condition")
                issues.append(f"Chronic Condition: {random.choice(CHRONIC_CONDITIONS)}")
            if "Palliative Care Need" in issues:
                issues.remove("Palliative Care Need")
                issues.append(f"Palliative Care Need: {random.choice(PALLIATIVE_CONDITIONS)}")
            if "Transplant Assessment" in issues:
                issues.remove("Transplant Assessment")
                issues.append(f"Transplant Assessment: {random.choice(TRANSPLANT_TYPES)}")
            
            if not issues: # If the list is still empty, assign default
                issues.append(NO_ILLNESS_REPORTED)
                chunk.loc[idx, "emt_remedies"] = ["N/A"]
                chunk.loc[idx, "hospital_remedies"] = ["Routine check-up"]
        
        # Convert list columns to JSON strings for CSV compatibility
        for col in ['assigned_issues', 'emt_remedies', 'hospital_remedies']:
            chunk[col] = chunk[col].apply(json.dumps)

        # Save the processed chunk
        if is_first_chunk:
            chunk.to_csv(output_csv_filepath, mode='w', header=True, index=False)
            is_first_chunk = False
        else:
            chunk.to_csv(output_csv_filepath, mode='a', header=False, index=False)
            
        logging.info(f"Processed and saved a chunk of {len(chunk)} records.")

    logging.info(f"Finished assigning illnesses. Final data saved to '{output_csv_filepath}'")


if __name__ == "__main__":
    assign_illnesses_chunked(PEOPLE_DATA_FILE, ILLNESSES_FILE)