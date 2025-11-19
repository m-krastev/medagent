"""
MOCK HOSPITAL INFORMATION SYSTEM (HIS) DATABASE
-----------------------------------------------
This file acts as a static database for the simulators.
In a real system, this would be an SQL database or FHIR server.
"""

LAB_REFERENCE_RANGES = {
    "WBC": {"low": 4.5, "high": 11.0, "unit": "K/uL"},
    "RBC": {"low": 4.5, "high": 5.9, "unit": "M/uL"},
    "HGB": {"low": 13.5, "high": 17.5, "unit": "g/dL"},
    "HCT": {"low": 41.0, "high": 50.0, "unit": "%"},
    "PLT": {"low": 150, "high": 450, "unit": "K/uL"},
    "NA": {"low": 135, "high": 145, "unit": "mmol/L"},
    "K": {"low": 3.5, "high": 5.0, "unit": "mmol/L"},
    "CL": {"low": 96, "high": 106, "unit": "mmol/L"},
    "CO2": {"low": 23, "high": 29, "unit": "mmol/L"},
    "BUN": {"low": 6, "high": 20, "unit": "mg/dL"},
    "CREATININE": {"low": 0.7, "high": 1.3, "unit": "mg/dL"},
    "GLUCOSE": {"low": 70, "high": 100, "unit": "mg/dL"},
    "CALCIUM": {"low": 8.5, "high": 10.2, "unit": "mg/dL"},
    "AST": {"low": 10, "high": 40, "unit": "U/L"},
    "ALT": {"low": 7, "high": 56, "unit": "U/L"},
    "ALP": {"low": 44, "high": 147, "unit": "U/L"},
    "BILIRUBIN": {"low": 0.1, "high": 1.2, "unit": "mg/dL"},
    "ALBUMIN": {"low": 3.4, "high": 5.4, "unit": "g/dL"},
    "PROTEIN": {"low": 6.0, "high": 8.3, "unit": "g/dL"},
    "TROPONIN": {"low": 0.0, "high": 0.04, "unit": "ng/mL"},
    "CK-MB": {"low": 0.0, "high": 5.0, "unit": "ng/mL"},
    "BNP": {"low": 0.0, "high": 100.0, "unit": "pg/mL"},
    "D-DIMER": {"low": 0.0, "high": 500.0, "unit": "ng/mL FEU"},
    "LACTATE": {"low": 0.5, "high": 1.0, "unit": "mmol/L"},
    "CRP": {"low": 0.0, "high": 10.0, "unit": "mg/L"},
    "ESR": {"low": 0.0, "high": 20.0, "unit": "mm/hr"},
    "TSH": {"low": 0.4, "high": 4.0, "unit": "mIU/L"},
    "FREE_T4": {"low": 0.8, "high": 1.8, "unit": "ng/dL"},
    "A1C": {"low": 4.0, "high": 5.6, "unit": "%"},
}

# Disease Profiles for Simulation Logic
# Maps keywords in the "context" to lab abnormalities
DISEASE_PROFILES = {
    "infection": {"WBC": "HIGH", "CRP": "HIGH", "LACTATE": "HIGH"},
    "sepsis": {"WBC": "HIGH", "LACTATE": "CRITICAL", "BP": "LOW"},
    "anemia": {"HGB": "LOW", "HCT": "LOW", "RBC": "LOW"},
    "kidney_failure": {"CREATININE": "CRITICAL", "BUN": "HIGH", "K": "HIGH"},
    "heart_attack": {"TROPONIN": "CRITICAL", "CK-MB": "HIGH"},
    "heart_failure": {"BNP": "HIGH"},
    "liver_failure": {"ALT": "HIGH", "AST": "HIGH", "BILIRUBIN": "HIGH", "ALBUMIN": "LOW"},
    "diabetes": {"GLUCOSE": "HIGH", "A1C": "HIGH"},
    "dehydration": {"NA": "HIGH", "BUN": "HIGH"},
    "pe": {"D-DIMER": "HIGH"},
}
