"""
Imaging Agent Tools - Radiology ordering and simulation
"""

import logging
from google.adk.tools.tool_context import ToolContext
from typing import Optional, List, Literal # Import Literal

import random
import numpy as np
import pydicom
import nibabel as nib
from nibabel.nifti1 import Nifti1Image # Import Nifti1Image for type hinting
from skimage import filters, feature
from skimage.transform import resize

from .models import LabResult, ImagingReport
from .mock_data import LAB_REFERENCE_RANGES, DISEASE_PROFILES

# Configure logging for imaging tools
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
        elif "abdomen" in reg:
            logger.debug(f"[ImagingSimulator] Region matched: abdomen")
            if "appendicitis" in ctx:
                findings = "Dilated appendix (12mm) with periappendiceal fat stranding."
                impression = "Acute Appendicitis."
                logger.debug(f"[ImagingSimulator] Pattern matched: appendicitis")

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


from typing import Optional, List # Import Optional and List for type hints

# =========================
# TOOL WRAPPERS
# =========================


def tool_order_labs(test_name: str, clinical_context: str = "") -> str:
    logger.info(f"[TOOL] tool_order_labs CALLED - test_name: '{test_name}', clinical_context: '{clinical_context[:50] if clinical_context else 'None'}...'")
    result = lab_sim.order_test(test_name, clinical_context)
    logger.info(f"[TOOL] tool_order_labs COMPLETED - result: {result}")
    return str(result)


def tool_extract_slice(path: str, slice_index: Optional[int] = None):
    logger.info(f"[TOOL] tool_extract_slice CALLED - path: '{path}', slice_index: {slice_index}")
    img = img_feat_extractor.load_image(path)
    slice_img = img_feat_extractor.extract_slice(img, slice_index)
    logger.info(f"[TOOL] tool_extract_slice COMPLETED - slice shape: {slice_img.shape}")
    return slice_img.tolist()


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
