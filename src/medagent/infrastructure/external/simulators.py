import random
from typing import List
from ...domain.models import LabResult, ImagingReport
from ...infrastructure.external.mock_data import LAB_REFERENCE_RANGES, DISEASE_PROFILES


class MRIReport:
    """Represents an MRI analysis report."""
    def __init__(self, region: str, sequences: List[str], findings: str, impression: str):
        self.region = region
        self.sequences = sequences
        self.findings = findings
        self.impression = impression
    
    def __str__(self):
        seq_str = ", ".join(self.sequences)
        return (f"MRI {self.region.upper()}\n"
                f"Sequences: {seq_str}\n"
                f"Findings: {self.findings}\n"
                f"Impression: {self.impression}")


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


class MRISimulator:
    """
    Simulates MRI image loading and analysis.
    Provides detailed MRI interpretation based on region and clinical context.
    """
    
    def analyze_mri_slice(self, region: str, clinical_context: str = "") -> MRIReport:
        """
        Simulates loading and analyzing an MRI image slice.
        Args:
            region: Anatomical region (brain, spine, etc.)
            clinical_context: Clinical indication for the MRI
        Returns:
            MRIReport with detailed findings
        """
        reg = region.lower()
        ctx = clinical_context.lower()
        
        # Default sequences for different regions
        sequences = []
        findings = ""
        impression = ""
        
        if "brain" in reg or "head" in reg:
            sequences = ["T1", "T2", "FLAIR", "DWI"]
            
            if "stroke" in ctx or "ischemic" in ctx:
                findings = (
                    "T2/FLAIR: Hyperintense signal in the left MCA territory involving the left frontal and temporal lobes. "
                    "DWI: Restricted diffusion in the same distribution confirming acute infarction. "
                    "No significant mass effect. No hemorrhagic transformation."
                )
                impression = "Acute ischemic stroke in the left MCA territory."
                
            elif "hemorrhage" in ctx or "bleed" in ctx:
                findings = (
                    "T1: Hyperintense signal in the right basal ganglia. "
                    "T2: Hypointense center with surrounding hyperintense edema. "
                    "GRE/SWI: Blooming artifact confirming hemorrhage. "
                    "Moderate mass effect with 3mm midline shift."
                )
                impression = "Acute intraparenchymal hemorrhage in the right basal ganglia with mass effect."
                
            elif "tumor" in ctx or "mass" in ctx:
                findings = (
                    "T1: Hypointense mass in the right frontal lobe measuring 3.2 x 2.8 cm. "
                    "T2/FLAIR: Hyperintense with surrounding vasogenic edema. "
                    "Post-contrast: Heterogeneous enhancement with central necrosis. "
                    "Mass effect with 5mm midline shift."
                )
                impression = "High-grade glioma versus metastasis. Recommend biopsy for tissue diagnosis."
                
            elif "ms" in ctx or "multiple sclerosis" in ctx or "demyelinating" in ctx:
                findings = (
                    "FLAIR: Multiple hyperintense periventricular white matter lesions in a perpendicular orientation to the corpus callosum (Dawson fingers). "
                    "T2: Additional lesions in the juxtacortical and infratentorial regions. "
                    "T1 post-contrast: Some lesions show enhancement suggesting active inflammation."
                )
                impression = "Multiple demyelinating lesions consistent with Multiple Sclerosis."
                
            else:
                findings = (
                    "Normal brain parenchyma with age-appropriate volume loss. "
                    "No acute infarction, hemorrhage, or mass lesion. "
                    "Ventricular system is normal in size and configuration. "
                    "No abnormal enhancement."
                )
                impression = "Normal brain MRI for age."
                
        elif "spine" in reg or "cervical" in reg or "lumbar" in reg or "thoracic" in reg:
            sequences = ["T1", "T2", "STIR"]
            
            if "herniation" in ctx or "disc" in ctx:
                findings = (
                    "T2: Posterior disc herniation at L4-L5 with compression of the left L5 nerve root. "
                    "Disc desiccation at multiple levels. "
                    "Moderate spinal canal stenosis at L4-L5. "
                    "Facet arthropathy at multiple levels."
                )
                impression = "L4-L5 disc herniation with left L5 radiculopathy."
                
            elif "cord" in ctx or "myelopathy" in ctx:
                findings = (
                    "T2: Increased intramedullary signal at C5-C6 level. "
                    "T1: Hypointense signal in the same region. "
                    "Mild cord expansion. "
                    "No abnormal enhancement."
                )
                impression = "Cervical cord signal abnormality concerning for myelitis or early myelomalacia."
                
            else:
                findings = (
                    "Normal vertebral body alignment and height. "
                    "Spinal cord demonstrates normal signal intensity. "
                    "No disc herniation or significant spinal canal stenosis. "
                    "Paravertebral soft tissues are unremarkable."
                )
                impression = "Normal spine MRI."
                
        elif "knee" in reg or "shoulder" in reg or "joint" in reg:
            sequences = ["T1", "T2", "PD"]
            findings = "Normal joint space, intact ligaments and tendons. No effusion or abnormal signal."
            impression = "Normal MRI of the joint."
            
        else:
            sequences = ["T1", "T2"]
            findings = f"Normal MRI appearance of the {region}. No acute abnormality detected."
            impression = "Normal study."
        
        return MRIReport(
            region=region,
            sequences=sequences,
            findings=findings,
            impression=impression
        )


# Singleton Instances
lab_sim = LabSimulator()
img_sim = ImagingSimulator()
mri_sim = MRISimulator()

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

def tool_analyze_mri(region: str, clinical_context: str = "") -> str:
    """
    [TOOL] Analyzes a sample MRI image slice for the specified region.
    This tool simulates loading an MRI image and provides detailed radiological interpretation.
    
    Args:
        region: Anatomical region to analyze (e.g., 'brain', 'spine', 'knee')
        clinical_context: Clinical indication for the MRI study
    
    Returns:
        Detailed MRI analysis report with sequences, findings, and impression
    """
    report = mri_sim.analyze_mri_slice(region, clinical_context)
    return str(report)
