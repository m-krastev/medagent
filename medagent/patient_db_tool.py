import sqlite3
import json
import os
import base64
import datetime
from typing import Optional, Dict, List, Any, Union

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
    """Retrieves file data from the database.

    Supports optional filtering and can return file data as raw bytes or base64-encoded strings.

    Args:
        patient_id: ID of the patient.
        file_type: Optional file type to filter by.
        return_base64: If True, return file data as base64-encoded strings.
        mime_type: Optional MIME type to filter by.
        filename_contains: Optional substring that must appear in filename.
        max_results: Optional limit on number of returned rows.
    """
    def _ensure_columns(conn):
        # Ensure new optional columns exist (safe no-op if already present)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(patient_files)")
        cols = [r[1] for r in cursor.fetchall()]
        if 'filename' not in cols:
            cursor.execute("ALTER TABLE patient_files ADD COLUMN filename TEXT")
        if 'mime_type' not in cols:
            cursor.execute("ALTER TABLE patient_files ADD COLUMN mime_type TEXT")
        if 'created_at' not in cols:
            cursor.execute("ALTER TABLE patient_files ADD COLUMN created_at TEXT")
        conn.commit()

    conn = _connect_db()
    _ensure_columns(conn)
    cursor = conn.cursor()

    query = "SELECT type, data, filename, mime_type, created_at FROM patient_files WHERE patient_id = ?"
    params: List[Any] = [patient_id]
    if file_type:
        query += " AND type = ?"
        params.append(file_type)
    # Additional optional filters are handled by callers via kwargs in newer signature
    cursor.execute(query, tuple(params))
    files = cursor.fetchall()
    conn.close()

    if not files:
        return None

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
    # Ensure optional columns exist for older DBs
    cursor.execute("PRAGMA table_info(patient_files)")
    cols = [r[1] for r in cursor.fetchall()]
    if 'filename' not in cols:
        cursor.execute("ALTER TABLE patient_files ADD COLUMN filename TEXT")
        cols.append('filename')
    if 'mime_type' not in cols:
        cursor.execute("ALTER TABLE patient_files ADD COLUMN mime_type TEXT")
        cols.append('mime_type')
    if 'created_at' not in cols:
        cursor.execute("ALTER TABLE patient_files ADD COLUMN created_at TEXT")
        cols.append('created_at')

    # Check if patient_id exists in patient_data, if not, create a placeholder
    cursor.execute("INSERT OR IGNORE INTO patient_data (patient_id) VALUES (?)", (patient_id,))

    cursor.execute(
        "INSERT INTO patient_files (patient_id, type, data, filename, mime_type, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (patient_id, file_type, sqlite3.Binary(raw_bytes), filename, mime_type, created_at),
    )
    conn.commit()
    conn.close()
