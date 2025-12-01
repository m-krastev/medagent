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
    # Hepatobiliary labs
    "BILIRUBIN": {"low": 0.3, "high": 1.0, "unit": "mg/dL"},
    "ALT": {"low": 0, "high": 35, "unit": "U/L"},
    "AST": {"low": 0, "high": 35, "unit": "U/L"},
    "ALP": {"low": 30, "high": 120, "unit": "U/L"},
    "GGT": {"low": 8, "high": 61, "unit": "U/L"},
    "LIPASE": {"low": 0, "high": 160, "unit": "U/L"},
    "AMYLASE": {"low": 25, "high": 125, "unit": "U/L"},
    # Additional common labs
    "BNP": {"low": 0, "high": 100, "unit": "pg/mL"},
    "PROCALCITONIN": {"low": 0, "high": 0.1, "unit": "ng/mL"},
}

# Disease Profiles for Simulation
DISEASE_PROFILES = {
    "infection": {"WBC": "HIGH", "CRP": "HIGH", "LACTATE": "HIGH", "PROCALCITONIN": "HIGH"},
    "sepsis": {"WBC": "CRITICAL", "CRP": "HIGH", "LACTATE": "CRITICAL", "PROCALCITONIN": "CRITICAL"},
    "anemia": {"HGB": "LOW"},
    "kidney_failure": {"CREATININE": "CRITICAL", "K": "HIGH"},
    "heart_attack": {"TROPONIN": "CRITICAL"},
    "pe": {"D-DIMER": "HIGH"},
    "diabetes": {"GLUCOSE": "HIGH"},
    # Hepatobiliary diseases
    "cholecystitis": {"WBC": "HIGH", "CRP": "HIGH", "BILIRUBIN": "HIGH", "ALP": "HIGH", "GGT": "HIGH"},
    "cholangitis": {"WBC": "CRITICAL", "BILIRUBIN": "HIGH", "ALP": "HIGH", "ALT": "HIGH", "AST": "HIGH", "GGT": "HIGH"},
    "choledocholithiasis": {"BILIRUBIN": "HIGH", "ALP": "HIGH", "GGT": "HIGH"},
    "pancreatitis": {"LIPASE": "CRITICAL", "AMYLASE": "CRITICAL", "WBC": "HIGH", "CRP": "HIGH"},
    "hepatitis": {"ALT": "CRITICAL", "AST": "CRITICAL", "BILIRUBIN": "HIGH"},
    "liver_abscess": {"WBC": "CRITICAL", "ALP": "HIGH", "CRP": "HIGH", "PROCALCITONIN": "HIGH"},
    # Pyelonephritis
    "pyelonephritis": {"WBC": "HIGH", "CRP": "HIGH", "CREATININE": "HIGH", "PROCALCITONIN": "HIGH"},
}
