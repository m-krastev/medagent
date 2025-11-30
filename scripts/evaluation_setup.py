import pandas as pd
import sqlite3
import json
import os
import datetime
import requests
import zipfile
import io
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from medagent.patient_db_tool import (
    store_patient_data_in_db,
    store_patient_lab_results_in_db,
    store_patient_file_in_db,
    _connect_db # Import _connect_db from the tool, as it's consistent now
)

# Login using e.g. `huggingface-cli login` to access this dataset
splits = {"dev": "MM/dev.jsonl", "test": "MM/test.jsonl"}
dataset_path = "hf://datasets/TsinghuaC3I/MedXpertQA/" + splits["dev"]
# db_path is now managed by patient_db_tool._connect_db, or can be set here if preferred
# If set here, ensure it matches DB_PATH in patient_db_tool.py
# Using "data/patient_db.sqlite" explicitly
db_path = "data/patient_db.sqlite" 

IMAGE_DATASET_URL = (
    "https://huggingface.co/datasets/TsinghuaC3I/MedXpertQA/resolve/main/images.zip"
)
IMAGE_DIR = Path("data/images")


def setup_database():
    conn = _connect_db() # Use the imported _connect_db
    cursor = conn.cursor()

    # Create patient_data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_data (
            patient_id TEXT PRIMARY KEY,
            question TEXT,
            options TEXT,
            label TEXT,
            medical_task TEXT,
            body_system TEXT,
            question_type TEXT
        )
    """)

    # Create patient_files table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_files (
            patient_id TEXT,
            type TEXT,
            data BLOB,
            filename TEXT,
            mime_type TEXT,
            created_at TEXT,
            FOREIGN KEY (patient_id) REFERENCES patient_data(patient_id)
        )
    """)

    # Create patient_lab_results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_lab_results (
            patient_id TEXT,
            lab_results_string TEXT,
            FOREIGN KEY (patient_id) REFERENCES patient_data(patient_id)
        )
    """)
    conn.commit()
    conn.close()

# _ensure_patient_files_columns is no longer needed here as patient_db_tool functions handle individual existence.
# The table creation in setup_database ensures the schema.


def populate_database(df: pd.DataFrame, temp_image_dir: Path):
    image_count = 0
    for index, row in df.iterrows():
        patient_id = row["id"]
        question = row["question"]
        options = row.get("options")  # Pass dict directly, store_patient_data_in_db will dump to JSON
        label = row.get("label")
        medical_task = row.get("medical_task")
        body_system = row.get("body_system")
        question_type = row.get("question_type")

        # Use the atomic store_patient_data_in_db function from patient_db_tool
        store_patient_data_in_db(
            patient_id=patient_id,
            question=question,
            options=options,
            label=label,
            medical_task=medical_task,
            body_system=body_system,
            question_type=question_type
        )

        # Use the atomic store_patient_lab_results_in_db function from patient_db_tool
        store_patient_lab_results_in_db(
            patient_id=patient_id,
            lab_results_string=None # None maps to NULL in SQLite
        )

        # Handle images if present in the dataset row
        if "images" in row and isinstance(row["images"], list):
            for image_filename in row["images"]:
                # Adjust path to account for the nested 'images' directory
                image_path = temp_image_dir / "images" / image_filename
                if image_path.is_file():
                    try:
                        with open(image_path, "rb") as f:
                            image_data = f.read()

                        # Determine mime type from suffix
                        mime_type = f"image/{image_path.suffix.lower().lstrip('.')}"
                        if image_path.suffix.lower() == ".jpg":
                            mime_type = "image/jpeg"

                        # Use the atomic store_patient_file_in_db function from patient_db_tool
                        store_patient_file_in_db(
                            patient_id=patient_id,
                            file_type="image",
                            file_data=image_data,
                            filename=image_filename,
                            mime_type=mime_type,
                        )
                        image_count += 1
                    except Exception as e:
                        print(
                            f"Error storing image {image_filename} for patient {patient_id}: {e}"
                        )
                else:
                    print(
                        f"Image file not found: {image_path} for patient {patient_id}"
                    )
    
    print(
        f"Database populated with {len(df)} entries from {dataset_path} and {image_count} images."
    )


def download_and_extract_images() -> Path:
    """Downloads the image zip file and extracts it to a temporary directory.
    Returns the path to the extracted directory.
    """
    print(f"Downloading images from {IMAGE_DATASET_URL}...")
    response = requests.get(IMAGE_DATASET_URL, stream=True)
    response.raise_for_status()  # Raise an exception for HTTP errors

    # Create the image directory if it doesn't exist
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    temp_extract_dir = IMAGE_DIR / "temp_extracted"
    if temp_extract_dir.exists():
        import shutil

        shutil.rmtree(temp_extract_dir)  # Clean up previous extraction if it exists
    temp_extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        print(f"Extracting images to {temp_extract_dir}...")
        zf.extractall(temp_extract_dir)

    print("Image extraction complete.")
    return temp_extract_dir


if __name__ == "__main__":
    import shutil

    print(f"Setting up database at {db_path}...")
    setup_database()
    print("Populating database...")

    df = pd.read_json(dataset_path, lines=True)  # Read DF once

    temp_image_dir = download_and_extract_images()  # Download and extract images
    populate_database(
        df, temp_image_dir
    )  # Pass extracted image dir to populate function

    # Clean up temporary extracted directory
    if temp_image_dir.exists():
        shutil.rmtree(temp_image_dir)
        print(f"Cleaned up temporary image directory: {temp_image_dir}")

    print("Database setup and population complete.")
