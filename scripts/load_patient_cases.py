#!/usr/bin/env python3
"""
Script to load patient cases from examples/ into the SQLite database.

This reads .txt files from the examples/ directory and stores them in the
patient_data table with the patient ID derived from the filename.
"""

import os
import sys
import glob
import sqlite3
import json

EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "patient_db.sqlite")


def _connect_db():
    """Establishes a connection to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def store_patient_data(patient_id: str, description: str, metadata: dict = None):
    """Store patient data in the database."""
    conn = _connect_db()
    cursor = conn.cursor()
    metadata_json = json.dumps(metadata) if metadata else None
    
    cursor.execute(
        """
        INSERT OR REPLACE INTO patient_data (
            patient_id, description, metadata
        ) VALUES (?, ?, ?)
        """,
        (patient_id, description, metadata_json)
    )
    conn.commit()
    conn.close()


def load_patient_cases():
    """Load all patient case files from examples/ directory into the database."""
    
    # Find all .txt files in examples/
    case_files = glob.glob(os.path.join(EXAMPLES_DIR, "*.txt"))
    
    if not case_files:
        print(f"No .txt files found in {EXAMPLES_DIR}")
        return
    
    print(f"Found {len(case_files)} patient case files")
    
    for case_file in sorted(case_files):
        # Extract patient ID from filename (e.g., MM-2000.txt -> MM-2000)
        filename = os.path.basename(case_file)
        patient_id = os.path.splitext(filename)[0]
        
        # Read the case content
        with open(case_file, 'r', encoding='utf-8') as f:
            description = f.read().strip()
        
        # Store in database
        store_patient_data(
            patient_id=patient_id,
            description=description,
            metadata={"source_file": filename}
        )
        
        print(f"  ✓ Loaded {patient_id} ({len(description)} chars)")
    
    print(f"\n✅ Successfully loaded {len(case_files)} patient cases into database")


def verify_database():
    """Verify the database contents after loading."""
    conn = _connect_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT patient_id, LENGTH(description) as desc_len FROM patient_data")
    rows = cursor.fetchall()
    
    print("\nDatabase contents:")
    print("-" * 40)
    for row in rows:
        print(f"  {row['patient_id']}: {row['desc_len']} chars")
    
    conn.close()


if __name__ == "__main__":
    print("Loading patient cases into database...")
    print("=" * 50)
    load_patient_cases()
    verify_database()
