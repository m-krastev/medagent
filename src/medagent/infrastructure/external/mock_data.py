# Lab Reference Ranges
LAB_REFERENCE_RANGES = {
    "WBC": {"low": 4.5, "high": 11.0, "unit": "x10^9/L"},
    "HGB": {"low": 13.5, "high": 17.5, "unit": "g/dL"},
    "PLT": {"low": 150, "high": 450, "unit": "x10^9/L"},
    "NA": {"low": 135, "high": 145, "unit": "mmol/L"},
    "K": {"low": 3.5, "high": 5.0, "unit": "mmol/L"},
    "CREATININE": {"low": 0.7, "high": 1.3, "unit": "mg/dL"},
    "GLUCOSE": {"low": 70, "high": 100, "unit": "mg/dL"},
    "TROPONIN": {"low": 0.0, "high": 0.04, "unit": "ng/mL"},
    "D-DIMER": {"low": 0.0, "high": 0.5, "unit": "mg/L FEU"},
    "LACTATE": {"low": 0.5, "high": 2.2, "unit": "mmol/L"},
    "CRP": {"low": 0.0, "high": 10.0, "unit": "mg/L"},
    "TSH": {"low": 0.4, "high": 4.0, "unit": "mIU/L"},
}

# Disease Profiles for Simulation
DISEASE_PROFILES = {
    "infection": {"WBC": "HIGH", "CRP": "HIGH", "LACTATE": "HIGH"},
    "sepsis": {"WBC": "CRITICAL", "CRP": "HIGH", "LACTATE": "CRITICAL", "BP": "LOW"},
    "anemia": {"HGB": "LOW"},
    "kidney_failure": {"CREATININE": "CRITICAL", "K": "HIGH"},
    "heart_attack": {"TROPONIN": "CRITICAL"},
    "pe": {"D-DIMER": "HIGH"},
    "diabetes": {"GLUCOSE": "HIGH"},
}
