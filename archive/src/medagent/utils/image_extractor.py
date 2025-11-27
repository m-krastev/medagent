import numpy as np
import pydicom
import nibabel as nib
from skimage import filters, feature
from skimage.transform import resize

class ImageFeatureExtractor:
    """
    Safe, non-diagnostic MRI/DICOM feature extractor.
    Computes purely technical image metrics.
    """

    def load_image(self, path):
        """
        Loads:
        - DICOM (.dcm)
        - NIfTI (.nii / .nii.gz)
        - NumPy arrays (.npy)
        """

        path = str(path).lower()

        if path.endswith(".dcm"):
            ds = pydicom.dcmread(path)
            return ds.pixel_array.astype(np.float32)

        elif path.endswith(".nii") or path.endswith(".nii.gz"):
            img = nib.load(path)
            return img.get_fdata().astype(np.float32)

        elif path.endswith(".npy"):
            return np.load(path).astype(np.float32)

        else:
            raise ValueError("Unsupported file format.")

    def extract_slice(self, img, slice_index=None):
        """
        Extracts a 2D slice from 2D or 3D image volume.
        """

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
        density = edges.mean()
        return float(density)

    def compute_contrast_index(self, slice_img):
        p1, p99 = np.percentile(slice_img, [1, 99])
        contrast = float(p99 - p1)
        return contrast

    def compute_symmetry_score(self, slice_img):
        h, w = slice_img.shape
        mid = w // 2
        
        left = slice_img[:, :mid]
        right = slice_img[:, w-mid:]
        right_flipped = np.fliplr(right)

        left_resized = resize(left, right_flipped.shape)
        diff = np.mean(np.abs(left_resized - right_flipped))

        return float(1.0 / (1.0 + diff))

    def compute_noise_estimate(self, slice_img):
        median = filters.median(slice_img)
        noise = float(np.mean(np.abs(slice_img - median)))
        return noise

    def analyze(
        self,
        path,
        slice_index=None,
        operations=None,
        bins=64
    ):
        """
        Main entry point.
        Returns a dictionary of requested image features.
        """

        if operations is None:
            operations = ["histogram", "edges", "contrast", "symmetry", "noise"]

        img = self.load_image(path)
        slice_img = self.extract_slice(img, slice_index)

        results = {}

        if "histogram" in operations:
            hist, edges = self.compute_histogram(slice_img, bins=bins)
            results["histogram"] = {
                "bins": bins,
                "histogram": hist,
                "edges": edges
            }

        if "edges" in operations:
            results["edge_density"] = self.compute_edge_density(slice_img)

        if "contrast" in operations:
            results["contrast_index"] = self.compute_contrast_index(slice_img)

        if "symmetry" in operations:
            results["symmetry_score"] = self.compute_symmetry_score(slice_img)

        if "noise" in operations:
            results["noise_estimate"] = self.compute_noise_estimate(slice_img)

        return results
