import logging
import sqlite3
import json
import os
import base64
import datetime
from typing import Optional, Dict, List, Any, Union

DB_PATH = "data/patient_db.sqlite"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            filename TEXT,
            mime_type TEXT,
            created_at TEXT,
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
    """Retrieves patient data from the database.
    
    Returns data that may include:
    - description: The clinical case description/vignette
    - metadata: Additional structured data (JSON)
    - lab_results_string: Lab results if stored separately
    """
    conn = _connect_db()
    cursor = conn.cursor()

    # First try the actual schema (description, metadata)
    try:
        cursor.execute("""
            SELECT patient_id, description, metadata
            FROM patient_data 
            WHERE patient_id = ?
        """, (patient_id,))
        patient_data = cursor.fetchone()
    except sqlite3.OperationalError:
        # Fall back to legacy schema
        cursor.execute("""
            SELECT 
                patient_id, question, options, label, medical_task, body_system, question_type
            FROM patient_data 
            WHERE patient_id = ?
        """, (patient_id,))
        patient_data = cursor.fetchone()

    # Select lab results
    cursor.execute("SELECT lab_results_string FROM patient_lab_results WHERE patient_id = ?", (patient_id,))
    lab_results = cursor.fetchone()

    conn.close()

    if patient_data:
        result = dict(patient_data)
        
        # Parse metadata from JSON if present
        if 'metadata' in result and result['metadata']:
            try:
                result['metadata'] = json.loads(result['metadata'])
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Parse options from JSON string (legacy schema)
        if 'options' in result and result['options']:
            try:
                result['options'] = json.loads(result['options'])
            except (json.JSONDecodeError, TypeError):
                pass

        # Add lab results
        if lab_results:
            result['lab_results_string'] = lab_results['lab_results_string']
        else:
            result['lab_results_string'] = None
            
        return result
    return None

def get_patient_file_from_db(patient_id: str, file_type: Optional[str] = None, max_results: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
    """Retrieves file data from the database.

    Supports optional filtering and can return file data as raw bytes or base64-encoded strings.

    Args:
        patient_id: ID of the patient.
        file_type: Optional file type to filter by.
        max_results: Optional limit on number of returned rows.
    """
    
    conn = _connect_db()
    cursor = conn.cursor()

    query = "SELECT type, data, filename, mime_type, created_at FROM patient_files WHERE patient_id = ?"
    params: List[Any] = [patient_id]
    if file_type:
        query += " AND type = ?"
        params.append(file_type)
    if max_results is not None:
        query += " LIMIT ?"
        params.append(max_results)
    logging.info(f"Executing query: {query} with params: {params}")
    cursor.execute(query, tuple(params))
    files = cursor.fetchall()

    if not files:
        # If no matches are found, check for any matching patient_id
        cursor.execute("SELECT patient_id, type, data, filename, mime_type, created_at FROM patient_files WHERE patient_id = ?", (patient_id,))
        logging.info(f"No files found for patient_id={patient_id} with type={file_type}. Checking for any files with patient_id only.")
        files = cursor.fetchall()
        if not files:
            return None
    conn.close()

    result: List[Dict[str, Any]] = []
    for f in files:
        item = {
            "type": f[0],
            "data": f[1],
            "filename": f[2],
            "mime_type": f[3],
            "created_at": f[4],
        }
        result.append(item)
    return result

def store_patient_data_in_db(
    patient_id: str,
    description: str,
    metadata: Optional[Dict] = None,
) -> None:
    """Stores or updates patient data in the database using the actual schema.
    
    Args:
        patient_id: Unique patient identifier
        description: The clinical case description/vignette (includes lab results in text)
        metadata: Optional additional structured data
    """
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

def store_patient_lab_results_in_db(patient_id: str, lab_results_string: Optional[str]) -> None:
    """Stores or updates patient lab results in the database."""
    conn = _connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO patient_data (patient_id) VALUES (?)", (patient_id,))
    cursor.execute(
        "INSERT OR REPLACE INTO patient_lab_results (patient_id, lab_results_string) VALUES (?, ?)",
        (patient_id, lab_results_string)
    )
    conn.commit()
    conn.close()

def _ensure_bytes(data: Union[bytes, bytearray, memoryview, str]) -> bytes:
    """Convert various data types to raw bytes suitable for BLOB storage.

    Accepts bytes, bytearray, memoryview or base64-encoded strings (including data URIs).
    """
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    if isinstance(data, memoryview):
        return data.tobytes()
    if isinstance(data, str):
        if data.startswith("data:") and "," in data:
            data = data.split(",", 1)[1]
        try:
            return base64.b64decode(data)
        except Exception as e:
            raise ValueError("String file_data must be base64-encoded") from e
    raise TypeError("Unsupported file_data type for BLOB storage")


def store_patient_file_in_db(
    patient_id: str,
    file_type: str,
    file_data: Union[bytes, str, bytearray, memoryview],
    filename: Optional[str] = None,
    mime_type: Optional[str] = None,
    created_at: Optional[str] = None,
) -> None:
    """Stores a patient file in the database as a BLOB.

    `file_data` may be raw bytes or a base64-encoded string (optionally a data URI).
    The data is converted to bytes and stored using `sqlite3.Binary` to ensure
    proper BLOB behavior.

    Optional metadata `filename`, `mime_type`, and `created_at` can be provided.
    If `created_at` is not provided, the current UTC ISO timestamp will be used.
    """
    raw_bytes = _ensure_bytes(file_data)

    if created_at is None:
        created_at = datetime.datetime.utcnow().isoformat()

    conn = _connect_db()
    cursor = conn.cursor()
    # Check if patient_id exists in patient_data, if not, create a placeholder
    cursor.execute("INSERT OR IGNORE INTO patient_data (patient_id) VALUES (?)", (patient_id,))

    cursor.execute(
        "INSERT INTO patient_files (patient_id, type, data, filename, mime_type, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (patient_id, file_type, sqlite3.Binary(raw_bytes), filename, mime_type, created_at),
    )
    conn.commit()
    conn.close()
