"""
Imaging Agent Tools - Radiology ordering and image analysis

This module provides tools for the imaging agent to:
1. Order and retrieve lab results (from database ONLY - no simulation)
2. Order and retrieve imaging studies (from database ONLY - no simulation)
3. Analyze medical images (feature extraction from actual files)

All results come from the patient database. If data is not available,
the tool will indicate that the test/study needs to be ordered in real life.
"""

import logging
import re
import sys
from google.adk.tools.tool_context import ToolContext
from typing import Optional, List, Dict, Any

import numpy as np
import pydicom
import nibabel as nib
from nibabel.nifti1 import Nifti1Image
from skimage import filters, feature
from skimage.transform import resize

from .models import LabResult, ImagingReport

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
    logger.propagate = False


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
# SINGLETON
# =========================

img_feat_extractor = ImageFeatureExtractor()

logger.info("[ImagingTools] ImageFeatureExtractor initialized")


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
    Orders a laboratory test. Retrieves results from the patient database ONLY.
    
    If the lab result is not in the patient's record, it indicates the test
    would need to be ordered in real clinical practice.
    
    Args:
        test_name: Name of the lab test to order (e.g., "WBC", "CRP", "Troponin").
        clinical_context: The suspected condition or clinical reason for the test.
        tool_context: ADK tool context for accessing session state.
    
    Returns:
        Dictionary containing test results with status, value, unit, reference range, and flag.
        If not available, returns status "not_available" with guidance.
    """
    logger.info(f"[TOOL] ========== tool_order_labs CALLED ==========")
    logger.info(f"[TOOL] tool_order_labs - test_name: '{test_name}'")
    logger.info(f"[TOOL] tool_order_labs - clinical_context: '{clinical_context[:50] if clinical_context else 'None'}...'")
    
    # Try to get from database
    db_result = None
    patient_id = None
    
    if tool_context:
        patient_id = tool_context.state.get("patient_id")
        if patient_id:
            logger.info(f"[TOOL] tool_order_labs - Checking database for patient {patient_id}")
            patient_data = get_patient_data_from_db(patient_id)
            if patient_data:
                # Check lab_results_string first, then look in the question field for embedded labs
                lab_results_string = patient_data.get("lab_results_string") or ""
                question_text = patient_data.get("question", "")
                combined_text = f"{lab_results_string}\n{question_text}"
                
                logger.debug(f"[TOOL] tool_order_labs - Parsing lab results from patient data...")
                db_result = _parse_lab_results_from_db(combined_text, test_name)
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
        # No data available - do NOT simulate
        logger.info(f"[TOOL] tool_order_labs - Test '{test_name}' not found in patient record")
        response = {
            "status": "not_available",
            "test_name": test_name,
            "message": f"Lab test '{test_name}' is not available in the patient's record. In clinical practice, this test would need to be ordered. Consider if this test is critical for the diagnosis before ordering.",
            "source": "not_in_record"
        }
    
    # Store result in state if tool_context available
    if tool_context:
        lab_results = tool_context.state.get('temp:lab_results', [])
        lab_results.append(response)
        tool_context.state['temp:lab_results'] = lab_results
    
    logger.info(f"[TOOL] tool_order_labs COMPLETED - status: {response['status']}")
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
    [TOOL] Orders a radiology study. Checks the patient database for existing imaging reports.
    
    If imaging is not available in the patient's record, it indicates the study
    would need to be ordered in real clinical practice.
    
    Args:
        modality: CT, MRI, XRAY, US.
        region: Body part (Chest, Head, Abdomen, RUQ, etc.).
        clinical_context: The suspected condition.
        tool_context: ADK tool context for accessing session state.
    
    Returns:
        Radiology report if available, or guidance that the study needs to be ordered.
    """
    logger.info(f"[TOOL] ========== tool_order_imaging CALLED ==========")
    logger.info(f"[TOOL] tool_order_imaging - modality: '{modality}'")
    logger.info(f"[TOOL] tool_order_imaging - region: '{region}'")
    logger.info(f"[TOOL] tool_order_imaging - clinical_context: '{clinical_context[:100] if clinical_context else 'None'}...'")
    
    patient_id = None
    if tool_context:
        patient_id = tool_context.state.get("patient_id")
        logger.info(f"[TOOL] tool_order_imaging - patient_id from state: '{patient_id}'")
    else:
        logger.warning(f"[TOOL] tool_order_imaging - NO tool_context provided!")
    
    # Check if imaging data exists in the patient record
    imaging_info = None
    image_files = []
    radiology_images = []
    figure_descriptions = {}  # Maps figure letter to what it shows
    
    if patient_id:
        # Get patient data first to check clinical vignette
        patient_data = get_patient_data_from_db(patient_id)
        question_text = ""
        if patient_data:
            question_text = patient_data.get("question", "")
            
            # Parse Figure descriptions from clinical vignette
            # e.g., "A chest radiograph is shown in Figure A" -> {"a": "chest radiograph"}
            # e.g., "An ECG is shown in Figure A" -> {"a": "ecg"}
            # e.g., "An abdominal radiograph is obtained (figure)" -> {"a": "abdominal radiograph"}
            figure_patterns = [
                r'(?:A|An)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?(?:\s+of\s+the\s+\w+)?)\s+is\s+shown\s+in\s+[Ff]igure\s+([A-Za-z])',
                r'[Ff]igure\s+([A-Za-z])\s+shows?\s+(?:a|an)?\s*([A-Za-z]+(?:\s+[A-Za-z]+)?)',
                r'(?:His|Her|The)\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)\s+(?:is|are)\s+shown\s+in\s+[Ff]igure\s+([A-Za-z])',
                # Pattern for "(figure)" without letter - assume it's Figure A
                r'(?:A|An)\s+([\w\s]+?)\s+is\s+(?:obtained|shown|performed)(?:\s+today)?\s*\(figure\)',
                # Pattern for "X is performed and shown in Figure Y"
                r'(?:A|An)\s+([A-Za-z]+)\s+is\s+(?:quickly\s+)?performed\s+and\s+(?:is\s+)?shown\s+in\s+[Ff]igure\s+([A-Za-z])',
            ]
            for pattern in figure_patterns:
                matches = re.findall(pattern, question_text, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple) and len(match) == 2:
                        # Handle both orderings: (description, letter) or (letter, description)
                        if len(match[0]) == 1 and match[0].isalpha():
                            letter, desc = match[0].lower(), match[1].lower()
                        else:
                            desc, letter = match[0].lower(), match[1].lower()
                        figure_descriptions[letter] = desc
                    elif isinstance(match, str):
                        # Single group match (from "(figure)" pattern) - assume Figure A
                        figure_descriptions['a'] = match.lower()
            
            logger.debug(f"[TOOL] tool_order_imaging - Figure descriptions: {figure_descriptions}")
        
        # Check for image files in the database
        files = get_patient_file_from_db(patient_id, file_type="image")
        if files:
            image_files = [f for f in files if f.get("filename")]
            
            # Determine which images are radiology based on filename patterns OR clinical vignette
            for f in image_files:
                filename = f.get("filename", "").lower()
                mime = f.get("mime_type", "").lower()
                
                # Check if filename indicates radiology format
                is_radiology_format = any([
                    "dicom" in mime or "dcm" in filename,
                    "nifti" in mime or ".nii" in filename,
                    modality.lower() in filename,
                    "xray" in filename or "x-ray" in filename,
                    "mri" in filename,
                    "ultrasound" in filename or "us_" in filename,
                    "ct_" in filename or "_ct" in filename,
                    "radiograph" in filename,
                ])
                
                # Check if this image corresponds to a radiology study mentioned in vignette
                # e.g., MM-2003-a.jpeg -> check if Figure A is a radiograph
                is_radiology_from_vignette = False
                figure_match = re.search(r'-([a-z])\.', filename)
                if figure_match:
                    figure_letter = figure_match.group(1)
                    figure_desc = figure_descriptions.get(figure_letter, "")
                    # Check if figure description mentions radiology modalities
                    radiology_terms = ["radiograph", "x-ray", "xray", "ct", "mri", "ultrasound", 
                                      "sonograph", "echocardiogram", "echo", "scan", "imaging",
                                      "ecg", "electrocardiogram", "ekg"]
                    is_radiology_from_vignette = any(term in figure_desc for term in radiology_terms)
                    
                    # Fallback: search for radiology terms near the Figure reference in original text
                    if not is_radiology_from_vignette:
                        figure_context_pattern = rf'.{{0,50}}[Ff]igure\s+{figure_letter.upper()}.{{0,20}}'
                        context_match = re.search(figure_context_pattern, question_text, re.IGNORECASE)
                        if context_match:
                            context = context_match.group(0).lower()
                            is_radiology_from_vignette = any(term in context for term in radiology_terms)
                    
                    if is_radiology_from_vignette:
                        logger.info(f"[TOOL] tool_order_imaging - Figure {figure_letter.upper()} is '{figure_desc}' (radiology)")
                
                if is_radiology_format or is_radiology_from_vignette:
                    radiology_images.append(f)
            
            logger.info(f"[TOOL] tool_order_imaging - Found {len(image_files)} total images, {len(radiology_images)} radiology images")
        
        # Also try to extract imaging findings from the clinical text
        if patient_data:
            imaging_info = _extract_imaging_from_text(question_text, modality, region)
    else:
        logger.warning(f"[TOOL] tool_order_imaging - No patient_id available, cannot check database")
    
    # If we found radiology images matching the request, report them
    if radiology_images:
        file_list = ", ".join([f.get("filename", "unknown") for f in radiology_images])
        result = f"""IMAGING STUDY: {modality} {region}
STATUS: RADIOLOGY IMAGES AVAILABLE

The following radiology images are available for this patient:
{file_list}

Use the tool_analyze_image function to analyze specific image files if needed."""
        logger.info(f"[TOOL] tool_order_imaging - Found radiology images in patient record")
    elif imaging_info:
        result = f"IMAGING STUDY: {modality} {region}\nFINDINGS: {imaging_info['findings']}\nIMPRESSION: {imaging_info['impression']}"
        logger.info(f"[TOOL] tool_order_imaging - Found imaging data in patient record text")
    else:
        # No radiology imaging available - do NOT simulate
        # But mention if there are other images (physical exam photos)
        other_images_note = ""
        if image_files:
            file_list = ", ".join([f.get("filename", "unknown") for f in image_files])
            other_images_note = f"""
NOTE: The patient record contains clinical photos ({file_list}) which may be physical exam images (e.g., "Figure A"), not radiology studies. Review the clinical vignette to understand what these images show."""
        
        result = f"""IMAGING STUDY: {modality} {region}
STATUS: NOT AVAILABLE

This imaging study ({modality} {region}) has not been performed yet.
In clinical practice, this study would need to be ordered.

COST CONSIDERATION: {_get_imaging_cost_info(modality)}

Before ordering, consider:
- Is this imaging study critical for the diagnosis?
- Are there less expensive alternatives that could provide the same information?
- Has similar imaging been done recently that could be reviewed instead?{other_images_note}"""
        logger.info(f"[TOOL] tool_order_imaging - Imaging not in patient record")
    
    # Store in state if tool_context available
    if tool_context:
        imaging_reports = tool_context.state.get('temp:imaging_reports', [])
        imaging_reports.append({
            'modality': modality,
            'region': region,
            'result': result,
            'available': bool(radiology_images) or imaging_info is not None,
            'radiology_files': [f.get("filename") for f in radiology_images] if radiology_images else [],
            'other_image_files': [f.get("filename") for f in image_files if f not in radiology_images]
        })
        tool_context.state['temp:imaging_reports'] = imaging_reports
    
    logger.info(f"[TOOL] ========== tool_order_imaging END ==========")
    return result


def _extract_imaging_from_text(text: str, modality: str, region: str) -> Optional[Dict[str, str]]:
    """
    Extract imaging findings from clinical vignette text if an imaging study was ACTUALLY PERFORMED.
    
    This function looks for explicit mentions of imaging study RESULTS, not just
    anatomical references. Physical exam findings (auscultation, palpation) are NOT imaging.
    
    Returns findings only if there's clear evidence an imaging study was done and reported.
    """
    if not text:
        return None
    
    text_lower = text.lower()
    modality_lower = modality.lower()
    
    # Keywords that indicate an actual imaging study was performed and reported
    imaging_result_indicators = [
        "ct shows", "ct revealed", "ct demonstrates", "ct scan shows",
        "mri shows", "mri revealed", "mri demonstrates",
        "x-ray shows", "xray shows", "radiograph shows", "chest film shows",
        "ultrasound shows", "us shows", "sonography shows",
        "imaging shows", "imaging revealed", "imaging demonstrates",
        "ct of the", "mri of the", "x-ray of the", "ultrasound of the",
        "ct findings", "mri findings", "x-ray findings",
        "radiologic", "radiological", "radiology report",
    ]
    
    # Check if there's evidence an imaging study was actually done
    imaging_was_performed = False
    for indicator in imaging_result_indicators:
        if indicator in text_lower:
            imaging_was_performed = True
            break
    
    if not imaging_was_performed:
        # No imaging study appears to have been done
        return None
    
    # Now check if the specific modality was mentioned
    imaging_keywords = {
        "ct": ["ct ", "ct,", "ct.", "computed tomography", "cat scan"],
        "mri": ["mri ", "mri,", "mri.", "magnetic resonance"],
        "xray": ["x-ray", "xray", "radiograph", "chest film", "chest x"],
        "us": ["ultrasound", "ultrasonography", "sonography"]
    }
    
    modality_mentioned = False
    for keyword in imaging_keywords.get(modality_lower, [modality_lower]):
        if keyword in text_lower:
            modality_mentioned = True
            break
    
    if not modality_mentioned:
        return None
    
    # Try to extract findings
    findings_patterns = [
        rf"(?:{modality_lower}|ct|mri|x-ray|ultrasound)\s+(?:of\s+\w+\s+)?(?:shows?|reveals?|demonstrates?)[:\s]+([^.]+)",
        rf"(?:shows?|reveals?|demonstrates?)\s+([^.]+)(?:\s+on\s+{modality_lower})",
        r"(?:imaging\s+)?(?:findings?|impression)[:\s]+([^.]+)",
    ]
    
    for pattern in findings_patterns:
        match = re.search(pattern, text_lower)
        if match:
            return {
                "findings": match.group(1).strip().capitalize(),
                "impression": "See clinical vignette for imaging study details."
            }
    
    # If modality was mentioned with result indicators, but couldn't extract specific findings
    return {
        "findings": f"{modality.upper()} study was performed. Review clinical vignette for specific findings.",
        "impression": "Imaging study referenced in clinical presentation."
    }


def _get_imaging_cost_info(modality: str) -> str:
    """Return approximate cost tier for imaging modalities."""
    cost_tiers = {
        "MRI": "HIGH COST ($1,000-$3,000+) - Reserve for soft tissue, neurological, or musculoskeletal indications",
        "CT": "MODERATE-HIGH COST ($500-$1,500) - Consider radiation exposure",
        "US": "LOW-MODERATE COST ($200-$500) - Good first-line for abdominal, pelvic, vascular",
        "XRAY": "LOW COST ($100-$300) - Appropriate for bones, chest screening"
    }
    return cost_tiers.get(modality.upper(), "COST VARIES - Confirm with radiology")

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
