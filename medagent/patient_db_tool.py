import sqlite3
import json
import os
from typing import Optional, Dict, List, Any

DB_PATH = "data/patient_db.sqlite"

def _connect_db():
    """Establishes a connection to the SQLite database."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables dictionary-like access to rows
    return conn

def _create_tables():
    """Creates the necessary tables if they don't exist."""
    conn = _connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_data (
            patient_id TEXT PRIMARY KEY,
            description TEXT,
            metadata TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_files (
            patient_id TEXT,
            type TEXT,
            data BLOB,
            FOREIGN KEY (patient_id) REFERENCES patient_data(patient_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_lab_results (
            patient_id TEXT,
            lab_results_string TEXT,
            FOREIGN KEY (patient_id) REFERENCES patient_data(patient_id)
        )
    """)
    conn.commit()
    conn.close()

# Ensure tables are created when the module is imported
_create_tables()

def get_patient_data_from_db(patient_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves patient data and lab results from the database."""
    conn = _connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT description, metadata FROM patient_data WHERE patient_id = ?", (patient_id,))
    patient_data = cursor.fetchone()

    cursor.execute("SELECT lab_results_string FROM patient_lab_results WHERE patient_id = ?", (patient_id,))
    lab_results = cursor.fetchone()

    conn.close()

    if patient_data:
        result = dict(patient_data)
        if lab_results:
            result['lab_results_string'] = lab_results['lab_results_string']
        else:
            result['lab_results_string'] = None
        if result['metadata']:
            result['metadata'] = json.loads(result['metadata'])
        return result
    return None

def get_patient_file_from_db(patient_id: str, file_type: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """Retrieves file data from the database."""
    conn = _connect_db()
    cursor = conn.cursor()

    if file_type:
        cursor.execute("SELECT type, data FROM patient_files WHERE patient_id = ? AND type = ?", (patient_id, file_type))
    else:
        cursor.execute("SELECT type, data FROM patient_files WHERE patient_id = ?", (patient_id,))
    
    files = cursor.fetchall()
    conn.close()

    if files:
        return [{"type": f['type'], "data": f['data']} for f in files]
    return None

def store_patient_data_in_db(patient_id: str, description: str, metadata: Optional[Dict] = None) -> None:
    """Stores or updates patient data in the database."""
    conn = _connect_db()
    cursor = conn.cursor()
    metadata_json = json.dumps(metadata) if metadata else None
    cursor.execute(
        "INSERT OR REPLACE INTO patient_data (patient_id, description, metadata) VALUES (?, ?, ?)",
        (patient_id, description, metadata_json)
    )
    conn.commit()
    conn.close()

def store_patient_lab_results_in_db(patient_id: str, lab_results_string: str) -> None:
    """Stores or updates patient lab results in the database."""
    conn = _connect_db()
    cursor = conn.cursor()
    # Check if patient_id exists in patient_data, if not, create a placeholder
    cursor.execute("INSERT OR IGNORE INTO patient_data (patient_id) VALUES (?)", (patient_id,))
    cursor.execute(
        "INSERT OR REPLACE INTO patient_lab_results (patient_id, lab_results_string) VALUES (?, ?)",
        (patient_id, lab_results_string)
    )
    conn.commit()
    conn.close()

def store_patient_file_in_db(patient_id: str, file_type: str, file_data: bytes) -> None:
    """Stores a patient file in the database."""
    conn = _connect_db()
    cursor = conn.cursor()
    # Check if patient_id exists in patient_data, if not, create a placeholder
    cursor.execute("INSERT OR IGNORE INTO patient_data (patient_id) VALUES (?)", (patient_id,))
    cursor.execute(
        "INSERT INTO patient_files (patient_id, type, data) VALUES (?, ?, ?)",
        (patient_id, file_type, file_data)
    )
    conn.commit()
    conn.close()
