import pandas as pd
import sqlite3
import json
import os

# Login using e.g. `huggingface-cli login` to access this dataset
splits = {'dev': 'MM/dev.jsonl', 'test': 'MM/test.jsonl'}
dataset_path = "hf://datasets/TsinghuaC3I/MedXpertQA/" + splits["dev"]
db_path = "data/patient_db.sqlite"

# Ensure the data directory exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

def setup_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create patient_data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_data (
            patient_id TEXT PRIMARY KEY,
            description TEXT,
            metadata TEXT
        )
    """)

    # Create patient_files table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_files (
            patient_id TEXT,
            type TEXT,
            data BLOB,
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

def populate_database():
    df = pd.read_json(dataset_path, lines=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for index, row in df.iterrows():
        patient_id = row['id']
        description = row['question']
        
        metadata = {
            "medical_task": row.get('medical_task'),
            "body_system": row.get('body_system'),
            "question_type": row.get('question_type'),
            "options": row.get('options'),
            "label": row.get('label')
        }
        metadata_json = json.dumps(metadata)

        # Insert into patient_data
        cursor.execute(
            "INSERT OR REPLACE INTO patient_data (patient_id, description, metadata) VALUES (?, ?, ?)",
            (patient_id, description, metadata_json)
        )

        # Insert into patient_lab_results (with NULL for lab_results_string)
        cursor.execute(
            "INSERT OR REPLACE INTO patient_lab_results (patient_id, lab_results_string) VALUES (?, ?)",
            (patient_id, None) # None maps to NULL in SQLite
        )
    
    conn.commit()
    conn.close()
    print(f"Database populated with {len(df)} entries from {dataset_path}")

if __name__ == "__main__":
    print(f"Setting up database at {db_path}...")
    setup_database()
    print("Populating database...")
    populate_database()
    print("Database setup and population complete.")
