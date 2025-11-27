import random
import numpy as np
import pydicom
import nibabel as nib
from skimage import filters, feature
from skimage.transform import resize

from ...domain.models import LabResult, ImagingReport
from ...infrastructure.external.mock_data import LAB_REFERENCE_RANGES, DISEASE_PROFILES


# =========================
# LAB SIMULATOR
# =========================

class LabSimulator:
    """
    Simulates a Pathology Lab.
    Generates realistic values based on a 'hidden' clinical context.
    """

    def order_test(self, test_name: str, clinical_context: str) -> LabResult:
        test_key = test_name.upper()

        # Validate
        if test_key not in LAB_REFERENCE_RANGES:
            return LabResult(
                test_name=test_name,
                value=0.0,
                unit="N/A",
                reference_range="N/A",
                flag="NORMAL"
            )

        ref = LAB_REFERENCE_RANGES[test_key]

        # Context modifier
        modifier = "NORMAL"
        ctx = clinical_context.lower()

        for disease, profile in DISEASE_PROFILES.items():
            if disease in ctx and test_key in profile:
                modifier = profile[test_key]
                break

        # Generate value
        if modifier == "NORMAL":
            val = random.uniform(ref["low"], ref["high"])
        elif modifier == "HIGH":
            val = random.uniform(ref["high"], ref["high"] * 1.5)
        elif modifier == "LOW":
            val = random.uniform(ref["low"] * 0.5, ref["low"])
        elif modifier == "CRITICAL":
            val = random.uniform(ref["high"] * 2, ref["high"] * 5)
        else:
            val = 0.0

        return LabResult(
            test_name=test_key,
            value=round(val, 2),
            unit=ref["unit"],
            reference_range=f"{ref['low']}-{ref['high']}",
            flag=modifier
        )


# =========================
# IMAGING SIMULATOR
# =========================

class ImagingSimulator:
    """
    Simulates a Radiology Department.
    """

    def order_scan(self, modality: str, region: str, clinical_context: str) -> ImagingReport:
        ctx = clinical_context.lower()
        reg = region.lower()

        findings = "No acute abnormality identified. Normal study."
        impression = "Normal."

        # Chest patterns
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

        # Head patterns
        elif "head" in reg or "brain" in reg:
            if "stroke" in ctx:
                findings = "Loss of gray-white differentiation in the left MCA territory."
                impression = "Acute Ischemic Stroke."
            elif "bleed" in ctx:
                findings = "Hyperdense collection in the subarachnoid space."
                impression = "Subarachnoid Hemorrhage."

        # Abdomen patterns
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


# =========================
# IMAGE FEATURE EXTRACTOR
# =========================

class ImageFeatureExtractor:
    """
    Safe, non-diagnostic MRI/DICOM feature extractor.
    Computes technical image metrics only.
    """

    def load_image(self, path):
        path = str(path).lower()

        if path.endswith(".dcm"):
            ds = pydicom.dcmread(path)
            return ds.pixel_array.astype(np.float32)

        if path.endswith(".nii") or path.endswith(".nii.gz"):
            img = nib.load(path)
            return img.get_fdata().astype(np.float32)

        if path.endswith(".npy"):
            return np.load(path).astype(np.float32)

        raise ValueError("Unsupported file format.")

    def extract_slice(self, img, slice_index=None):
        if img.ndim == 2:
            return img

        if img.ndim == 3:
            if slice_index is None:
                slice_index = img.shape[2] // 2
            return img[:, :, slice_index]

        if img.ndim == 4:
            if slice_index is None:
                slice_index = img.shape[3] // 2
            return img[:, :, :, slice_index]

        raise ValueError("Image must be 2D, 3D, or 4D.")

    def compute_histogram(self, slice_img, bins=64):
        hist, edges = np.histogram(slice_img, bins=bins, density=True)
        return hist.tolist(), edges.tolist()

    def compute_edge_density(self, slice_img):
        edges = feature.canny(slice_img / (slice_img.max() + 1e-6))
        return float(edges.mean())

    def compute_contrast_index(self, slice_img):
        p1, p99 = np.percentile(slice_img, [1, 99])
        return float(p99 - p1)

    def compute_symmetry_score(self, slice_img):
        h, w = slice_img.shape
        mid = w // 2

        left = slice_img[:, :mid]
        right = slice_img[:, w - mid:]
        right_flipped = np.fliplr(right)

        left_resized = resize(left, right_flipped.shape)
        diff = np.mean(np.abs(left_resized - right_flipped))

        return float(1.0 / (1.0 + diff))

    def compute_noise_estimate(self, slice_img):
        median = filters.median(slice_img)
        return float(np.mean(np.abs(slice_img - median)))

    def analyze(self, path, slice_index=None, operations=None, bins=64):
        if operations is None:
            operations = ["histogram", "edges", "contrast", "symmetry", "noise"]

        img = self.load_image(path)
        slice_img = self.extract_slice(img, slice_index)

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

        return results


# =========================
# SINGLETONS
# =========================

lab_sim = LabSimulator()
img_sim = ImagingSimulator()
img_feat_extractor = ImageFeatureExtractor()


# =========================
# TOOL WRAPPERS
# =========================

def tool_order_labs(test_name: str, clinical_context: str = "") -> str:
    result = lab_sim.order_test(test_name, clinical_context)
    return str(result)


def tool_order_imaging(modality: str, region: str, clinical_context: str = "") -> str:
    report = img_sim.order_scan(modality, region, clinical_context)
    return (
        f"REPORT ID: {report.id}\n"
        f"FINDINGS: {report.findings}\n"
        f"IMPRESSION: {report.impression}"
    )


def tool_analyze_image(path: str, slice_index: int = None, operations=None, bins: int = 64):
    return img_feat_extractor.analyze(path, slice_index, operations, bins)


def tool_extract_slice(path: str, slice_index: int = None):
    img = img_feat_extractor.load_image(path)
    slice_img = img_feat_extractor.extract_slice(img, slice_index)
    return slice_img.tolist()
