"""
Imaging Agent Tools - Radiology ordering and simulation

This module provides tools for the imaging agent to:
1. Order and retrieve lab results (from database or simulation)
2. Order and retrieve imaging studies (from database or simulation)
3. Analyze medical images (feature extraction)

Priority: Database > Simulation (fallback)
"""

import logging
import re
import sys
from google.adk.tools.tool_context import ToolContext
from typing import Optional, List, Literal, Dict, Any

import random
import numpy as np
import pydicom
import nibabel as nib
from nibabel.nifti1 import Nifti1Image # Import Nifti1Image for type hinting
from skimage import filters, feature
from skimage.transform import resize

from .models import LabResult, ImagingReport
from .mock_data import LAB_REFERENCE_RANGES, DISEASE_PROFILES

# Import database functions for real data access
from ...patient_db_tool import (
    get_patient_data_from_db,
    get_patient_file_from_db,
)

# Configure logging for imaging tools - ensure output to console
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add console handler if not already present
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(name)s] %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False


# =========================
# LAB SIMULATOR
# =========================


class LabSimulator:
    """
    Simulates a Pathology Lab.
    Generates realistic values based on a 'hidden' clinical context.
    """

    def order_test(self, test_name: str, clinical_context: str) -> LabResult:
        logger.info(f"[LabSimulator] order_test called - test_name: '{test_name}', clinical_context: '{clinical_context[:100] if clinical_context else 'None'}...'")
        test_key = test_name.upper()

        # Validate
        if test_key not in LAB_REFERENCE_RANGES:
            logger.warning(f"[LabSimulator] Test '{test_key}' not found in LAB_REFERENCE_RANGES. Returning default result.")
            return LabResult(
                test_name=test_name,
                value=0.0,
                unit="N/A",
                reference_range="N/A",
                flag="NORMAL", # This is already Literal compatible
            )

        ref = LAB_REFERENCE_RANGES[test_key]
        logger.debug(f"[LabSimulator] Reference range for '{test_key}': {ref}")

        # Context modifier
        modifier: Literal["NORMAL", "HIGH", "LOW", "CRITICAL"] = "NORMAL" # Explicitly type as Literal
        ctx = clinical_context.lower()

        for disease, profile in DISEASE_PROFILES.items():
            if disease in ctx and test_key in profile:
                # Ensure assigned values are also Literal compatible
                if profile[test_key] in ["NORMAL", "HIGH", "LOW", "CRITICAL"]:
                    modifier = profile[test_key] # type: ignore # type: ignore [assignment]
                    logger.debug(f"[LabSimulator] Disease '{disease}' matched in context. Modifier set to: {modifier}")
                break

        # Generate value
        # Explicitly cast to float to avoid type errors with random.uniform and multiplication
        ref_low = float(ref["low"])
        ref_high = float(ref["high"])

        if modifier == "NORMAL":
            val = random.uniform(ref_low, ref_high)
        elif modifier == "HIGH":
            val = random.uniform(ref_high, ref_high * 1.5)
        elif modifier == "LOW":
            val = random.uniform(ref_low * 0.5, ref_low)
        elif modifier == "CRITICAL":
            val = random.uniform(ref_high * 2, ref_high * 5)
        else:
            val = 0.0

        result = LabResult(
            test_name=test_key,
            value=round(val, 2),
            unit=str(ref["unit"]), # Ensure unit is string
            reference_range=f"{ref_low}-{ref_high}",
            flag=modifier,
        )
        logger.info(f"[LabSimulator] order_test completed - Result: {result}")
        return result


# =========================
# IMAGING SIMULATOR
# =========================


class ImagingSimulator:
    """
    Simulates a Radiology Department.
    """

    def order_scan(
        self, modality: str, region: str, clinical_context: str
    ) -> ImagingReport:
        logger.info(f"[ImagingSimulator] order_scan called - modality: '{modality}', region: '{region}', clinical_context: '{clinical_context[:100] if clinical_context else 'None'}...'")
        ctx = clinical_context.lower()
        reg = region.lower()

        findings = "No acute abnormality identified. Normal study."
        impression = "Normal."

        # Chest patterns
        if "chest" in reg:
            logger.debug(f"[ImagingSimulator] Region matched: chest")
            if "pneumonia" in ctx:
                findings = (
                    "Focal consolidation in the right lower lobe with air bronchograms."
                )
                impression = "Right Lower Lobe Pneumonia."
                logger.debug(f"[ImagingSimulator] Pattern matched: pneumonia")
            elif "heart_failure" in ctx:
                findings = "Cardiomegaly with interstitial edema and Kerley B lines."
                impression = "Pulmonary Edema consistent with CHF."
                logger.debug(f"[ImagingSimulator] Pattern matched: heart_failure")
            elif "pe" in ctx and "ct" in modality.lower():
                findings = "Filling defect in the right main pulmonary artery."
                impression = "Acute Pulmonary Embolism."
                logger.debug(f"[ImagingSimulator] Pattern matched: PE with CT")

        # Head patterns
        elif "head" in reg or "brain" in reg:
            logger.debug(f"[ImagingSimulator] Region matched: head/brain")
            if "stroke" in ctx:
                findings = (
                    "Loss of gray-white differentiation in the left MCA territory."
                )
                impression = "Acute Ischemic Stroke."
                logger.debug(f"[ImagingSimulator] Pattern matched: stroke")
            elif "bleed" in ctx:
                findings = "Hyperdense collection in the subarachnoid space."
                impression = "Subarachnoid Hemorrhage."
                logger.debug(f"[ImagingSimulator] Pattern matched: bleed")

        # Abdomen patterns
        elif "abdomen" in reg or "ruq" in reg or "right upper quadrant" in reg or "biliary" in reg or "gallbladder" in reg or "liver" in reg:
            logger.debug(f"[ImagingSimulator] Region matched: abdomen/biliary")
            if "appendicitis" in ctx:
                findings = "Dilated appendix (12mm) with periappendiceal fat stranding."
                impression = "Acute Appendicitis."
                logger.debug(f"[ImagingSimulator] Pattern matched: appendicitis")
            elif "cholecystitis" in ctx:
                if "us" in modality.lower() or "ultrasound" in modality.lower():
                    findings = "Gallbladder wall thickening (5mm), pericholecystic fluid, positive sonographic Murphy sign. Multiple gallstones identified."
                    impression = "Acute Cholecystitis."
                else:
                    findings = "Distended gallbladder with wall thickening and pericholecystic inflammatory changes. Gallstones present."
                    impression = "Acute Cholecystitis."
                logger.debug(f"[ImagingSimulator] Pattern matched: cholecystitis")
            elif "cholangitis" in ctx or "biliary" in ctx:
                findings = "Dilated common bile duct (12mm) with intrahepatic biliary dilatation. Possible distal CBD stone."
                impression = "Biliary obstruction with findings concerning for Cholangitis."
                logger.debug(f"[ImagingSimulator] Pattern matched: cholangitis/biliary")
            elif "choledocholithiasis" in ctx:
                findings = "Common bile duct dilation (10mm) with echogenic focus in the distal CBD consistent with choledocholithiasis."
                impression = "Choledocholithiasis with biliary obstruction."
                logger.debug(f"[ImagingSimulator] Pattern matched: choledocholithiasis")
            elif "pancreatitis" in ctx:
                findings = "Pancreatic enlargement with peripancreatic fat stranding and fluid collections."
                impression = "Acute Pancreatitis."
                logger.debug(f"[ImagingSimulator] Pattern matched: pancreatitis")
            elif "abscess" in ctx or "liver abscess" in ctx:
                findings = "Heterogeneous hepatic lesion with peripheral enhancement, measuring 5cm in the right lobe. Central hypodensity with possible gas locules."
                impression = "Hepatic abscess."
                logger.debug(f"[ImagingSimulator] Pattern matched: liver abscess")
            elif "pyelonephritis" in ctx or "kidney infection" in ctx:
                findings = "Right kidney shows focal areas of decreased enhancement with perinephric fat stranding."
                impression = "Acute Pyelonephritis, right kidney."
                logger.debug(f"[ImagingSimulator] Pattern matched: pyelonephritis")
            elif "sepsis" in ctx and ("source" in ctx or "focus" in ctx):
                # Generic abdominal sepsis workup - look for common sources
                findings = "Hepatic lesion with peripheral rim enhancement in the right lobe, concerning for abscess. No biliary dilatation. Kidneys show no hydronephrosis."
                impression = "Suspected hepatic abscess - recommend clinical correlation and possible drainage."
                logger.debug(f"[ImagingSimulator] Pattern matched: sepsis source")

        report = ImagingReport(
            modality=modality, region=region, findings=findings, impression=impression
        )
        logger.info(f"[ImagingSimulator] order_scan completed - Report ID: {report.id}, Impression: '{impression}'")
        return report


# =========================
# IMAGE FEATURE EXTRACTOR
# =========================


class ImageFeatureExtractor:
    """
    Safe, non-diagnostic MRI/DICOM feature extractor.
    Computes technical image metrics only.
    """

    def load_image(self, path):
        logger.info(f"[ImageFeatureExtractor] load_image called - path: '{path}'")
        path_lower = str(path).lower()

        if path_lower.endswith(".dcm"):
            logger.debug(f"[ImageFeatureExtractor] Loading DICOM file")
            ds = pydicom.dcmread(path)
            img = ds.pixel_array.astype(np.float32)
            logger.debug(f"[ImageFeatureExtractor] DICOM loaded - shape: {img.shape}")
            return img

        if path_lower.endswith(".nii") or path_lower.endswith(".nii.gz"):
            logger.debug(f"[ImageFeatureExtractor] Loading NIfTI file")
            img_nib: Nifti1Image = nib.load(path) # type: ignore [assignment]
            img = img_nib.get_fdata().astype(np.float32)
            logger.debug(f"[ImageFeatureExtractor] NIfTI loaded - shape: {img.shape}")
            return img

        if path_lower.endswith(".npy"):
            logger.debug(f"[ImageFeatureExtractor] Loading NumPy file")
            img = np.load(path).astype(np.float32)
            logger.debug(f"[ImageFeatureExtractor] NumPy loaded - shape: {img.shape}")
            return img

        logger.error(f"[ImageFeatureExtractor] Unsupported file format: {path}")
        raise ValueError(f"Unsupported file format: {path}")

    def extract_slice(self, img, slice_index=None):
        logger.debug(f"[ImageFeatureExtractor] extract_slice called - img.ndim: {img.ndim}, slice_index: {slice_index}")
        
        if img.ndim == 2:
            logger.debug(f"[ImageFeatureExtractor] 2D image, returning as-is")
            return img

        if img.ndim == 3:
            if slice_index is None:
                slice_index = img.shape[2] // 2
            logger.debug(f"[ImageFeatureExtractor] 3D image, extracting slice {slice_index}")
            return img[:, :, slice_index]

        if img.ndim == 4:
            if slice_index is None:
                slice_index = img.shape[3] // 2
            logger.debug(f"[ImageFeatureExtractor] 4D image, extracting slice {slice_index}")
            return img[:, :, :, slice_index]

        logger.error(f"[ImageFeatureExtractor] Image must be 2D, 3D, or 4D. Got {img.ndim}D")
        raise ValueError("Image must be 2D, 3D, or 4D.")

    def compute_histogram(self, slice_img, bins=64):
        logger.debug(f"[ImageFeatureExtractor] compute_histogram - bins: {bins}")
        hist, edges = np.histogram(slice_img, bins=bins, density=True)
        return hist.tolist(), edges.tolist()

    def compute_edge_density(self, slice_img):
        logger.debug(f"[ImageFeatureExtractor] compute_edge_density")
        edges = feature.canny(slice_img / (slice_img.max() + 1e-6))
        result = float(edges.mean())
        logger.debug(f"[ImageFeatureExtractor] edge_density: {result}")
        return result

    def compute_contrast_index(self, slice_img):
        logger.debug(f"[ImageFeatureExtractor] compute_contrast_index")
        p1, p99 = np.percentile(slice_img, [1, 99])
        result = float(p99 - p1)
        logger.debug(f"[ImageFeatureExtractor] contrast_index: {result}")
        return result

    def compute_symmetry_score(self, slice_img):
        logger.debug(f"[ImageFeatureExtractor] compute_symmetry_score")
        h, w = slice_img.shape
        mid = w // 2

        left = slice_img[:, :mid]
        right = slice_img[:, w - mid :]
        right_flipped = np.fliplr(right)

        left_resized = resize(left, right_flipped.shape)
        diff = np.mean(np.abs(left_resized - right_flipped))

        result = float(1.0 / (1.0 + diff))
        logger.debug(f"[ImageFeatureExtractor] symmetry_score: {result}")
        return result

    def compute_noise_estimate(self, slice_img):
        logger.debug(f"[ImageFeatureExtractor] compute_noise_estimate")
        median = filters.median(slice_img)
        result = float(np.mean(np.abs(slice_img - median)))
        logger.debug(f"[ImageFeatureExtractor] noise_estimate: {result}")
        return result

    def analyze(self, path, slice_index=None, operations=None, bins=64):
        logger.info(f"[ImageFeatureExtractor] analyze called - path: '{path}', slice_index: {slice_index}, operations: {operations}, bins: {bins}")
        
        if operations is None:
            operations = ["histogram", "edges", "contrast", "symmetry", "noise"]
            logger.debug(f"[ImageFeatureExtractor] Using default operations: {operations}")

        img = self.load_image(path)
        slice_img = self.extract_slice(img, slice_index)
        logger.debug(f"[ImageFeatureExtractor] Slice extracted - shape: {slice_img.shape}")

        results = {}

        if "histogram" in operations:
            hist, edges = self.compute_histogram(slice_img, bins=bins)
            results["histogram"] = {"bins": bins, "histogram": hist, "edges": edges}

        if "edges" in operations:
            results["edge_density"] = self.compute_edge_density(slice_img)

        if "contrast" in operations:
            results["contrast_index"] = self.compute_contrast_index(slice_img)

        if "symmetry" in operations:
            results["symmetry_score"] = self.compute_symmetry_score(slice_img)

        if "noise" in operations:
            results["noise_estimate"] = self.compute_noise_estimate(slice_img)

        logger.info(f"[ImageFeatureExtractor] analyze completed - results keys: {list(results.keys())}")
        return results


# =========================
# SINGLETONS
# =========================

lab_sim = LabSimulator()
img_sim = ImagingSimulator()
img_feat_extractor = ImageFeatureExtractor()

logger.info("[ImagingTools] Singletons initialized: LabSimulator, ImagingSimulator, ImageFeatureExtractor")


# =========================
# DATABASE HELPERS
# =========================

def _parse_lab_results_from_db(lab_results_string: str, test_name: str) -> Optional[Dict[str, Any]]:
    """
    Parse lab results from the database string format to find a specific test.
    
    The database stores lab results as a formatted string like:
    | Leukocyte count (per mm3) | 14,200 | 4500–11,000 |
    | Creatinine (mg/dL) | 2.0 | 0.6–1.1 |
    
    Args:
        lab_results_string: The raw lab results string from database
        test_name: The test name to search for
        
    Returns:
        Dictionary with parsed lab result or None if not found
    """
    if not lab_results_string:
        return None
    
    test_key = test_name.upper()
    
    # Common lab name mappings
    lab_name_mappings = {
        "WBC": ["leukocyte", "wbc", "white blood cell", "white cell"],
        "HGB": ["hemoglobin", "hgb", "hb"],
        "PLT": ["platelet", "plt"],
        "CREATININE": ["creatinine", "cr"],
        "BILIRUBIN": ["bilirubin", "bili", "total bilirubin"],
        "ALP": ["alkaline phosphatase", "alp", "alk phos"],
        "AST": ["aspartate aminotransferase", "ast", "sgot"],
        "ALT": ["alanine aminotransferase", "alt", "sgpt"],
        "CRP": ["c-reactive protein", "crp"],
        "TROPONIN": ["troponin", "trop"],
        "D-DIMER": ["d-dimer", "d dimer"],
        "LIPASE": ["lipase"],
        "AMYLASE": ["amylase"],
        "GGT": ["gamma-glutamyl", "ggt", "gamma gt"],
        "BNP": ["bnp", "brain natriuretic"],
        "LACTATE": ["lactate", "lactic acid"],
        "GLUCOSE": ["glucose", "blood sugar"],
        "NA": ["sodium", "na+"],
        "K": ["potassium", "k+"],
        "HCT": ["hematocrit", "hct"],
    }
    
    # Get possible names for this test
    possible_names = lab_name_mappings.get(test_key, [test_key.lower()])
    
    # Parse each line looking for matching test
    for line in lab_results_string.split('\n'):
        line_lower = line.lower()
        
        for name in possible_names:
            if name in line_lower:
                # Try to extract value using regex patterns
                # Pattern 1: | Name | Value | Reference |
                pipe_match = re.search(r'\|\s*[^|]+\s*\|\s*([0-9.,]+)\s*\|\s*([0-9.,\-–]+)\s*\|?', line)
                if pipe_match:
                    try:
                        value = float(pipe_match.group(1).replace(',', ''))
                        ref_range = pipe_match.group(2).replace('–', '-')
                        
                        # Parse reference range to determine flag
                        ref_parts = ref_range.split('-')
                        flag = "normal"
                        if len(ref_parts) == 2:
                            ref_low = float(ref_parts[0].replace(',', ''))
                            ref_high = float(ref_parts[1].replace(',', ''))
                            if value > ref_high:
                                flag = "HIGH"
                            elif value < ref_low:
                                flag = "LOW"
                            else:
                                flag = "NORMAL"
                        
                        # Extract unit from the name part if present
                        unit_match = re.search(r'\(([^)]+)\)', line)
                        unit = unit_match.group(1) if unit_match else ""
                        
                        return {
                            "test_name": test_key,
                            "value": value,
                            "unit": unit,
                            "reference_range": ref_range,
                            "flag": flag,
                            "source": "database"
                        }
                    except (ValueError, IndexError):
                        continue
    
    return None


# =========================
# TOOL WRAPPERS
# =========================


def tool_order_labs(test_name: str, clinical_context: str = "", tool_context: Optional[ToolContext] = None) -> dict:
    """
    Orders a laboratory test. First checks the patient database for existing results,
    then falls back to simulation if not found.
    
    Args:
        test_name: Name of the lab test to order (e.g., "WBC", "CRP", "Troponin").
        clinical_context: The suspected condition or clinical reason for the test.
        tool_context: ADK tool context for accessing session state.
    
    Returns:
        Dictionary containing test results with status, value, unit, reference range, and flag.
    """
    logger.info(f"[TOOL] ========== tool_order_labs CALLED ==========")
    logger.info(f"[TOOL] tool_order_labs - test_name: '{test_name}'")
    logger.info(f"[TOOL] tool_order_labs - clinical_context: '{clinical_context[:50] if clinical_context else 'None'}...'")
    logger.info(f"[TOOL] tool_order_labs - tool_context available: {tool_context is not None}")
    
    # PRIORITY 1: Try to get from database
    db_result = None
    if tool_context:
        patient_id = tool_context.state.get("patient_id")
        if patient_id:
            logger.info(f"[TOOL] tool_order_labs - Checking database for patient {patient_id}")
            patient_data = get_patient_data_from_db(patient_id)
            if patient_data:
                lab_results_string = patient_data.get("lab_results_string") or patient_data.get("description", "")
                logger.debug(f"[TOOL] tool_order_labs - Found patient data, parsing lab results...")
                db_result = _parse_lab_results_from_db(lab_results_string, test_name)
                if db_result:
                    logger.info(f"[TOOL] tool_order_labs - Found {test_name} in database: {db_result['value']} {db_result['unit']}")
    
    if db_result:
        response = {
            "status": "success",
            "test_name": db_result["test_name"],
            "value": db_result["value"],
            "unit": db_result["unit"],
            "reference_range": db_result["reference_range"],
            "flag": db_result["flag"],
            "source": "patient_record"
        }
    else:
        # PRIORITY 2: Fall back to simulation
        logger.info(f"[TOOL] tool_order_labs - No database result, using simulation")
        result = lab_sim.order_test(test_name, clinical_context)
        response = {
            "status": "success",
            "test_name": result.test_name,
            "value": result.value,
            "unit": result.unit,
            "reference_range": result.reference_range,
            "flag": result.flag,
            "source": "simulation"
        }
    
    # Store result in state if tool_context available
    if tool_context:
        lab_results = tool_context.state.get('temp:lab_results', [])
        lab_results.append(response)
        tool_context.state['temp:lab_results'] = lab_results
        logger.debug(f"[TOOL] tool_order_labs - Stored result in state. Total lab results: {len(lab_results)}")
    
    logger.info(f"[TOOL] tool_order_labs COMPLETED - {response['test_name']}: {response['value']} {response['unit']} ({response['flag']}) [source: {response.get('source', 'unknown')}]")
    logger.info(f"[TOOL] ========== tool_order_labs END ==========")
    return response


def tool_extract_slice(path: str, slice_index: Optional[int] = None, tool_context: Optional[ToolContext] = None) -> dict:
    """
    Extracts a 2D slice from a 3D medical image volume (CT, MRI).
    
    Args:
        path: File path to the medical image (DICOM, NIfTI, or NumPy format).
        slice_index: Specific slice index to extract. If None, extracts the middle slice.
        tool_context: ADK tool context for accessing session state.
    
    Returns:
        Dictionary containing status, slice shape, and the extracted slice data.
    """
    logger.info(f"[TOOL] ========== tool_extract_slice CALLED ==========")
    logger.info(f"[TOOL] tool_extract_slice - path: '{path}'")
    logger.info(f"[TOOL] tool_extract_slice - slice_index: {slice_index}")
    logger.info(f"[TOOL] tool_extract_slice - tool_context available: {tool_context is not None}")
    
    try:
        img = img_feat_extractor.load_image(path)
        slice_img = img_feat_extractor.extract_slice(img, slice_index)
        
        # Store in state if tool_context available
        if tool_context:
            tool_context.state['temp:last_extracted_slice'] = {
                'path': path,
                'slice_index': slice_index,
                'shape': list(slice_img.shape)
            }
            logger.debug(f"[TOOL] tool_extract_slice - Stored slice info in state")
        
        response = {
            "status": "success",
            "shape": list(slice_img.shape),
            "slice_index": slice_index if slice_index is not None else "middle",
            "data": slice_img.tolist()
        }
        logger.info(f"[TOOL] tool_extract_slice COMPLETED - slice shape: {slice_img.shape}")
        logger.info(f"[TOOL] ========== tool_extract_slice END ==========")
        return response
    except Exception as e:
        logger.error(f"[TOOL] tool_extract_slice FAILED - error: {e}")
        logger.info(f"[TOOL] ========== tool_extract_slice END (ERROR) ==========")
        return {"status": "error", "message": str(e)}


def tool_order_imaging(modality: str, region: str, clinical_context: str = "", tool_context: Optional[ToolContext] = None) -> str:
    """
    [TOOL] Orders a radiology study.
    
    Args:
        modality: CT, MRI, XRAY, US.
        region: Body part (Chest, Head, Abdomen).
        clinical_context: The suspected condition.
        tool_context: ADK tool context for accessing session state.
    
    Returns:
        Radiology report with REPORT ID, FINDINGS, and IMPRESSION.
    """
    logger.info(f"[TOOL] ========== tool_order_imaging CALLED ==========")
    logger.info(f"[TOOL] tool_order_imaging - modality: '{modality}'")
    logger.info(f"[TOOL] tool_order_imaging - region: '{region}'")
    logger.info(f"[TOOL] tool_order_imaging - clinical_context: '{clinical_context[:100] if clinical_context else 'None'}...'")
    logger.info(f"[TOOL] tool_order_imaging - tool_context available: {tool_context is not None}")
    
    # If clinical_context not provided, try to get from state
    if not clinical_context and tool_context:
        differential = tool_context.state.get('temp:differential_diagnosis', [])
        logger.debug(f"[TOOL] tool_order_imaging - Retrieved differential from state: {differential}")
        if differential:
            clinical_context = str(differential[-1]) if isinstance(differential, list) else str(differential)
            logger.info(f"[TOOL] tool_order_imaging - Using clinical_context from state: '{clinical_context}'")
    
    report = img_sim.order_scan(modality, region, clinical_context)
    
    # Store result in state if tool_context available
    if tool_context:
        imaging_reports = tool_context.state.get('temp:imaging_reports', [])
        imaging_reports.append(report.model_dump())
        tool_context.state['temp:imaging_reports'] = imaging_reports
        logger.debug(f"[TOOL] tool_order_imaging - Stored report in state. Total reports: {len(imaging_reports)}")
    
    result = f"REPORT ID: {report.id}\nFINDINGS: {report.findings}\nIMPRESSION: {report.impression}"
    logger.info(f"[TOOL] tool_order_imaging COMPLETED - Report ID: {report.id}")
    logger.info(f"[TOOL] ========== tool_order_imaging END ==========")
    return result

def tool_analyze_image(path: str, slice_index: Optional[int] = None, operations: Optional[List[str]] = None, bins: int = 64, tool_context: Optional[ToolContext] = None):
    """
    [TOOL] Analyzes a medical image and extracts features.
    
    Args:
        path: File path to the medical image.
        slice_index: Specific slice index for 3D images.
        operations: List of analysis operations to perform.
        bins: Number of bins for histogram analysis.
        tool_context: ADK tool context for accessing session state.
    Returns:
        Dictionary of extracted image features. 
    """
    logger.info(f"[TOOL] ========== tool_analyze_image CALLED ==========")
    logger.info(f"[TOOL] tool_analyze_image - path: '{path}'")
    logger.info(f"[TOOL] tool_analyze_image - slice_index: {slice_index}")
    logger.info(f"[TOOL] tool_analyze_image - operations: {operations}")
    logger.info(f"[TOOL] tool_analyze_image - bins: {bins}")
    logger.info(f"[TOOL] tool_analyze_image - tool_context available: {tool_context is not None}")
    
    try:
        results = img_feat_extractor.analyze(path, slice_index, operations, bins)
        logger.info(f"[TOOL] tool_analyze_image - Analysis successful. Results keys: {list(results.keys())}")
    except Exception as e:
        logger.error(f"[TOOL] tool_analyze_image - Analysis FAILED with error: {e}")
        raise
    
    if tool_context:
        image_analyses = tool_context.state.get('temp:image_analyses', [])
        image_analyses.append({'path': path, 'results': results})
        tool_context.state['temp:image_analyses'] = image_analyses
        logger.debug(f"[TOOL] tool_analyze_image - Stored analysis in state. Total analyses: {len(image_analyses)}")
    
    logger.info(f"[TOOL] tool_analyze_image COMPLETED")
    logger.info(f"[TOOL] ========== tool_analyze_image END ==========")
    return results
