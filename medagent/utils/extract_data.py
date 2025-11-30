import os
from pathlib import Path
import pandas as pd
import kagglehub
from kagglehub.datasets import KaggleDatasetAdapter

class MIMICLoader:
    """
    Downloads and loads the MIMIC-IV Clinical Database Demo 2.2 automatically.
    Exposes core tables as pandas DataFrames.
    """

    def __init__(self):
        print("Downloading MIMIC-IV demo dataset from Kaggle...")

        # Download the dataset if not already cached
        self.labevents: pd.DataFrame = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            "montassarba/mimic-iv-clinical-database-demo-2-2",
            path="hosp/labevents.csv"
        )

        self.d_items: pd.DataFrame = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            "montassarba/mimic-iv-clinical-database-demo-2-2",
            path="hosp/d_labitems.csv"

        )

        self.admissions: pd.DataFrame = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            "montassarba/mimic-iv-clinical-database-demo-2-2",
            path="hosp/admissions.csv"
        )
        self.patients: pd.DataFrame = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            "montassarba/mimic-iv-clinical-database-demo-2-2",
            path="hosp/patients.csv"
        )

        # Create LAB_NAME column
        self._attach_lab_names()

    def _attach_lab_names(self):
        """Map itemid → human-readable lab label."""
        if self.labevents.empty or self.d_items.empty:
            return
        mapping = self.d_items.set_index("itemid")["label"].to_dict()
        self.labevents["LAB_NAME"] = self.labevents["itemid"].map(mapping)


mimic = MIMICLoader()
