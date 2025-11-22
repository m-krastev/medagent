import random
from ...domain.models import LabResult, ImagingReport
from ...infrastructure.external.mock_data import LAB_REFERENCE_RANGES, DISEASE_PROFILES

class LabSimulator:
    """
    Simulates a Pathology Lab.
    Generates realistic values based on a 'hidden' clinical context.
    """
    
    def order_test(self, test_name: str, clinical_context: str) -> LabResult:
        test_key = test_name.upper()
        
        # 1. Validate Test
        if test_key not in LAB_REFERENCE_RANGES:
            # Fallback for unknown tests
            return LabResult(
                test_name=test_name, value=0.0, unit="N/A", 
                reference_range="N/A", flag="NORMAL"
            )
            
        ref = LAB_REFERENCE_RANGES[test_key]
        
        # 2. Determine Modifier based on Context
        modifier = "NORMAL"
        context_lower = clinical_context.lower()
        
        for disease, profile in DISEASE_PROFILES.items():
            if disease in context_lower:
                if test_key in profile:
                    modifier = profile[test_key]
                    break
        
        # 3. Generate Value
        val = 0.0
        if modifier == "NORMAL":
            val = random.uniform(ref["low"], ref["high"])
        elif modifier == "HIGH":
            val = random.uniform(ref["high"], ref["high"] * 1.5)
        elif modifier == "LOW":
            val = random.uniform(ref["low"] * 0.5, ref["low"])
        elif modifier == "CRITICAL":
            # 50/50 chance of critical high vs critical low if not specified, 
            # but usually critical means high for things like Troponin
            val = random.uniform(ref["high"] * 2, ref["high"] * 5)

        return LabResult(
            test_name=test_key,
            value=round(val, 2),
            unit=ref["unit"],
            reference_range=f"{ref['low']}-{ref['high']}",
            flag=modifier
        )

class ImagingSimulator:
    """
    Simulates a Radiology Department.
    Uses simple keyword matching to generate findings.
    """
    
    def order_scan(self, modality: str, region: str, clinical_context: str) -> ImagingReport:
        ctx = clinical_context.lower()
        reg = region.lower()
        
        findings = "No acute abnormality identified. Normal study."
        impression = "Normal."
        
        if "chest" in reg:
            if "pneumonia" in ctx:
                findings = "Focal consolidation in the right lower lobe with air bronchograms."
                impression = "Right Lower Lobe Pneumonia."
            elif "heart_failure" in ctx:
                findings = "Cardiomegaly with interstitial edema and Kerley B lines."
                impression = "Pulmonary Edema consistent with CHF."
            elif "pe" in ctx and "ct" in modality.lower():
                findings = "Filling defect in the right main pulmonary artery."
                impression = "Acute Pulmonary Embolism."
                
        elif "head" in reg or "brain" in reg:
            if "stroke" in ctx:
                findings = "Loss of gray-white differentiation in the left MCA territory."
                impression = "Acute Ischemic Stroke."
            elif "bleed" in ctx:
                findings = "Hyperdense collection in the subarachnoid space."
                impression = "Subarachnoid Hemorrhage."
                
        elif "abdomen" in reg:
            if "appendicitis" in ctx:
                findings = "Dilated appendix (12mm) with periappendiceal fat stranding."
                impression = "Acute Appendicitis."

        return ImagingReport(
            modality=modality,
            region=region,
            findings=findings,
            impression=impression
        )

# Singleton Instances
lab_sim = LabSimulator()
img_sim = ImagingSimulator()

# --- Tool Wrappers for Agents ---

def tool_order_labs(test_name: str, clinical_context: str = "") -> str:
    """
    [TOOL] Orders a specific lab test.
    Args:
        test_name: The standard code/name of the test (e.g., WBC, TROPONIN).
        clinical_context: The suspected condition (e.g., 'infection', 'chest pain').
    """
    result = lab_sim.order_test(test_name, clinical_context)
    return str(result)

def tool_order_imaging(modality: str, region: str, clinical_context: str = "") -> str:
    """
    [TOOL] Orders a radiology study.
    Args:
        modality: CT, MRI, XRAY, US.
        region: Body part (Chest, Head, Abdomen).
        clinical_context: The suspected condition.
    """
    report = img_sim.order_scan(modality, region, clinical_context)
    return f"REPORT ID: {report.id}\nFINDINGS: {report.findings}\nIMPRESSION: {report.impression}"
