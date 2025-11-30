import os
from pathlib import Path
import pandas as pd
import kagglehub


class MIMICLoader:
    """
    Downloads and loads the MIMIC-IV Clinical Database Demo 2.2 automatically.
    Exposes core tables as pandas DataFrames.
    """

    def __init__(self):
        print("Downloading MIMIC-IV demo dataset from Kaggle...")

        # Download the dataset if not already cached
        dataset_path = kagglehub.dataset_download(
            "montassarba/mimic-iv-clinical-database-demo-2-2"
        )

        # The dataset has a subdirectory, so we need to find the actual data path
        base_path = Path(dataset_path)
        
        # Check if there's a subdirectory with the actual files
        subdirs = [d for d in base_path.iterdir() if d.is_dir() and 'mimic' in d.name.lower()]
        if subdirs:
            base_path = subdirs[0]

        self.base_path = base_path

        self.labevents = self._load("hosp/labevents.csv")
        self.d_items = self._load("hosp/d_labitems.csv")
        self.admissions = self._load("hosp/admissions.csv")
        self.patients = self._load("hosp/patients.csv")

        # Create LAB_NAME column
        self._attach_lab_names()

    def _load(self, relative_path: str):
        """Load a CSV into a pandas DataFrame."""
        full_path = self.base_path / relative_path
        if not full_path.exists():
            return pd.DataFrame()
        return pd.read_csv(full_path, low_memory=False)

    def _attach_lab_names(self):
        """Map itemid → human-readable lab label."""
        if self.labevents.empty or self.d_items.empty:
            return
        mapping = self.d_items.set_index("itemid")["label"].to_dict()
        self.labevents["LAB_NAME"] = self.labevents["itemid"].map(mapping)


mimic = MIMICLoader()
