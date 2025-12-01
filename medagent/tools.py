"""
Tools for Medical Orchestrator Root Agent
State management and workflow coordination tools for the diagnostic process.
"""

import asyncio
import json
import logging
import asyncio
import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Literal, Optional

from google.adk.tools import load_artifacts
from google.adk.tools.tool_context import ToolContext

from medagent.patient_db_tool import (
    get_patient_data_from_db,
    get_patient_file_from_db,
    store_patient_data_in_db,
    store_patient_file_in_db,
    store_patient_lab_results_in_db,
)

logger = logging.getLogger(__name__)

# ============================================================================
# STATE MANAGEMENT TOOLS
# ============================================================================


def load_patient_case(patient_id: str, tool_context: ToolContext) -> str:
    """
    Load a patient case from the database and set up the session state.
    This MUST be called before delegating to sub-agents so they can access patient data.
    
    Args:
        patient_id: The patient ID to load (e.g., "MM-2001", "MM-2000")
    
    Returns:
        Patient case summary or error message
    """
    logger.info(f"[load_patient_case] Loading patient case: {patient_id}")
    
    # Get patient data from database
    patient_data = get_patient_data_from_db(patient_id)
    
    if not patient_data:
        logger.error(f"[load_patient_case] Patient {patient_id} not found in database")
        return f"Error: Patient '{patient_id}' not found in the database. Use tool_get_database_status() to check if the database is loaded."
    
    # Store patient_id in state - THIS IS CRITICAL for sub-agents
    tool_context.state["patient_id"] = patient_id
    logger.info(f"[load_patient_case] Stored patient_id in state: {patient_id}")
    
    # Store other patient data in state
    question = patient_data.get("question", "")
    options = patient_data.get("options", {})
    label = patient_data.get("label", "")
    medical_task = patient_data.get("medical_task", "")
    body_system = patient_data.get("body_system", "")
    
    tool_context.state["clinical_vignette"] = question
    tool_context.state["answer_options"] = options
    tool_context.state["correct_answer"] = label
    tool_context.state["medical_task"] = medical_task
    tool_context.state["body_system"] = body_system
    
    # Check for patient files (images)
    files = get_patient_file_from_db(patient_id, file_type="image")
    image_count = len(files) if files else 0
    tool_context.state["patient_images"] = [f.get("filename") for f in files] if files else []
    
    logger.info(f"[load_patient_case] Loaded case with {image_count} images")
    
    # Format response
    response = f"""
=== PATIENT CASE LOADED: {patient_id} ===

**Clinical Vignette:**
{question[:500]}{'...' if len(question) > 500 else ''}

**Answer Options:**
{chr(10).join(f"({k}) {v}" for k, v in options.items()) if isinstance(options, dict) else options}

**Medical Task:** {medical_task}
**Body System:** {body_system}
**Images Available:** {image_count} file(s)

NOTE: Patient ID has been stored in session state. Sub-agents can now access patient data.
"""
    return response.strip()


def store_patient_data(field: str, value: Any, tool_context: ToolContext) -> str:
    """
    Store any patient data field in session state.
    NOTE: For bulk updates, prefer store_patient_data_multiple.

    Args:
        field: Field name (e.g., 'patient_id', 'patient_age', 'patient_sex', 'chief_complaint', 'location')
        value: Value to store (can be string, int, dict, list, etc.)

    Returns:
        Confirmation message
    """
    tool_context.state[field] = value
    logger.info(f"Stored {field}: {str(value)[:100]}...")
    return f"Successfully stored {field} in patient record"

def store_patient_data_multiple(data: Dict[str, Any], tool_context: ToolContext) -> str:
    """
    Store multiple patient data fields in session state.
    NOTE: SHOULD BE PREFERRED OVER store_patient_data FOR BULK UPDATES.

    Args:
        data: Dictionary of field names and their corresponding values.

    Returns:
        Confirmation message
    """
    for field, value in data.items():
        tool_context.state[field] = value
        logger.info(f"Stored {field}: {str(value)[:100]}...")
    return f"Successfully stored {len(data)} fields in patient record"

def get_patient_summary(tool_context: ToolContext) -> str:
    """
    Generate clinical summary from session state.
    Compiles all patient data stored in the session.

    Returns:
        Formatted clinical case summary
    """
    age = tool_context.state.get("patient_age", "Unknown")
    sex = tool_context.state.get("patient_sex", "Unknown")
    location = tool_context.state.get("location", "Unknown")
    complaint = tool_context.state.get("chief_complaint", "None")
    hpi = tool_context.state.get("history_present_illness", "")
    vitals = tool_context.state.get("vitals", {})
    labs = tool_context.state.get("lab_results", [])
    imaging = tool_context.state.get("imaging_reports", [])
    ddx = tool_context.state.get("differential_diagnosis", [])
    final_dx = tool_context.state.get("final_diagnosis", "")

    summary = f"""
=== CLINICAL CASE SUMMARY ===

DEMOGRAPHICS:
- Age: {age}
- Sex: {sex}
- Location: {location}

CHIEF COMPLAINT:
{complaint}

HISTORY OF PRESENT ILLNESS:
{hpi if hpi else "Not yet documented"}

VITALS:
{vitals if vitals else "Not recorded"}

LABORATORY RESULTS:
{labs if labs else "None ordered"}

IMAGING STUDIES:
{imaging if imaging else "None ordered"}

DIFFERENTIAL DIAGNOSIS:
{chr(10).join(f"- {d}" for d in ddx) if ddx else "Not yet formulated"}

FINAL DIAGNOSIS:
{final_dx if final_dx else "Pending"}
"""
    return summary.strip()


def update_differential_diagnosis(diagnosis: str, tool_context: ToolContext) -> str:
    """
    Add or update differential diagnosis list.

    Args:
        diagnosis: New or updated differential diagnosis from hypothesis agent

    Returns:
        Confirmation message
    """
    ddx_list = tool_context.state.get("differential_diagnosis", [])
    if isinstance(ddx_list, list):
        ddx_list.append(diagnosis)
    else:
        ddx_list = [diagnosis]
    tool_context.state["differential_diagnosis"] = ddx_list

    logger.info(f"Updated differential diagnosis (total: {len(ddx_list)})")
    return f"Differential diagnosis updated. Total diagnoses: {len(ddx_list)}"


def finalize_diagnosis(final_diagnosis: str, tool_context: ToolContext) -> str:
    """
    Store final diagnosis and mark case as complete.

    Args:
        final_diagnosis: The final diagnostic conclusion

    Returns:
        Confirmation message
    """
    tool_context.state["final_diagnosis"] = final_diagnosis
    tool_context.state["case_complete"] = True
    logger.info("Final diagnosis recorded")
    return f"Final diagnosis recorded and case marked complete"


def increment_diagnostic_loop(tool_context: ToolContext) -> str:
    """
    Increment and check diagnostic loop counter.

    Returns:
        Current iteration number
    """
    current = tool_context.state.get("diagnostic_loop_count", 0)
    current += 1
    tool_context.state["diagnostic_loop_count"] = current

    logger.info(f"Diagnostic loop iteration: {current}")
    return f"Diagnostic loop iteration {current}"


async def access_patient_database(
    query_type: Literal["data", "file", "lab_results"],
    tool_context: ToolContext,
    item_type: Optional[
        str
    ] = None,  # For files: "2D image", "CT", "MRI", "pathology slides", etc.
    description: Optional[str] = None,  # For storing new data
    lab_results_string: Optional[str] = None,  # For storing new lab results
) -> str:
    """
    Accesses or updates patient information in the central database.
    If information is not found, it will ask for further input from the user.

    Args:
        query_type: The type of information to query or store: "data", "file", "lab_results".
        item_type: (Optional) Required if query_type is "file". Specifies the type of file.
        description: (Optional) A description for patient_data when storing new data.
        lab_results_string: (Optional) Lab results string when storing new lab results.
        tool_context: The ADK context object for interacting with the user and artifacts.

    Returns:
        A message indicating the result of the operation, including retrieved data.
    """

    patient_id = tool_context.state.get("patient_id", None)
    if not patient_id:
        return "Error: patient_id not found in session state."

    # Ensure patient_id exists as a base entry if we are trying to store
    if query_type in ["data", "file", "lab_results"] and not get_patient_data_from_db(
        patient_id
    ):
        store_patient_data_in_db(
            patient_id=patient_id, 
            question=f"Placeholder entry for patient {patient_id}"
        )
        logger.info(f"Created placeholder entry for patient {patient_id} in DB.")

    if query_type == "data":
        patient_info = get_patient_data_from_db(patient_id)
        if patient_info and patient_info.get("question"): # Check for 'question' key
            response = (
                f"Patient Data for {patient_id}:\n"
                f"Question: {patient_info['question']}\n" # Use 'question'
                f"Options: {json.dumps(patient_info['options'])}" # Use 'options'
            )
            if patient_info.get("lab_results_string"):
                response += f"\nLab Results: {patient_info['lab_results_string']}"
            tool_context.state[f"patient_data_{patient_id}"] = patient_info
            return response
        else:
            # Ask for question (previously description)
            tool_confirmation = tool_context.tool_confirmation
            if not tool_confirmation:
                tool_context.request_confirmation(
                    hint=f"No patient data (question) found for {patient_id}. Please provide the main question or description for this patient.",
                    payload={"patient_id": patient_id, "data": ""},
                )
            user_input = tool_confirmation.payload.get("data", "")
            # Store user_input as 'question'
            store_patient_data_in_db(
                patient_id=patient_id, 
                question=user_input
            )
            tool_context.state[f"patient_data_{patient_id}"] = {
                "question": user_input, # Store as 'question'
                "options": None,
            }
            return f"Patient data (question) for {patient_id} stored: {user_input}"

    elif query_type == "lab_results":
        patient_info = get_patient_data_from_db(patient_id)
        if patient_info and patient_info.get("lab_results_string"):
            response = f"Patient {patient_id} Lab Results: {patient_info['lab_results_string']}"
            tool_context.state[f"patient_lab_results_{patient_id}"] = patient_info[
                "lab_results_string"
            ]
            return response
        else:
            # Ask for lab results
            tool_confirmation = tool_context.tool_confirmation
            if not tool_confirmation:
                tool_context.request_confirmation(
                    hint=f"No lab results found for {patient_id}. Please provide the lab results as a string.",
                    payload={"patient_id": patient_id, "lab_results": ""},
                )
                
            if not hasattr(tool_confirmation, 'payload'):
                return "Error: No lab results provided."
            user_input = tool_confirmation.payload.get("lab_results", "")
            store_patient_lab_results_in_db(patient_id, user_input)
            tool_context.state[f"patient_lab_results_{patient_id}"] = user_input
            return f"Patient {patient_id} lab results stored: {user_input}"

    elif query_type == "file":
        if not item_type:
            return "Error: item_type is required for query_type 'file'."

        files = get_patient_file_from_db(patient_id, item_type)
        if files:
            # Return metadata about the file, not the raw blob directly
            file_info = [{"type": f["type"], "size": len(f["data"])} for f in files]
            tool_context.state[f"patient_file_{patient_id}_{item_type}"] = file_info
            return f"Found {len(files)} files of type '{item_type}' for patient {patient_id}: {file_info}"
        else:
            # Ask for file upload
            tool_confirmation = tool_context.tool_confirmation
            if not tool_confirmation:
                tool_context.request_confirmation(
                    hint=f"No '{item_type}' file found for {patient_id}. Please upload the file using the ADK file picker, then type 'DONE'.",
                    payload={"patient_id": patient_id, "item_type": item_type},
                )
            user_response = tool_confirmation.payload.get("user_response", "")

            if user_response.lower() == "done":
                artifacts = await tool_context.list_artifacts()
                if not artifacts:
                    return "No file uploaded. Please upload a file and try again."

                most_recent_file = artifacts[-1]
                try:
                    artifact_content = await tool_context.load_artifact(
                        filename=most_recent_file
                    )
                    data_bytes = artifact_content.inline_data.data

                    if data_bytes is None:
                        return f"Error: No data found in uploaded artifact '{most_recent_file}'."

                    store_patient_file_in_db(patient_id, item_type, data_bytes)
                    tool_context.state[f"patient_file_{patient_id}_{item_type}"] = {
                        "type": item_type,
                        "size": len(data_bytes),
                    }
                    return f"'{item_type}' file for patient {patient_id} uploaded and stored. Size: {len(data_bytes)} bytes."
                except Exception as e:
                    return f"Error processing uploaded file: {e}"
            else:
                return "File upload cancelled by user."

    return "Invalid query_type specified."


async def get_patient_raw_file_and_path(
    file_type: str,
    tool_context: ToolContext,
) -> str:
    """
    Retrieves a patient file (image, document, etc.) from the database,
    saves it to a temporary local file, and returns the path to that file.
    The temporary file will be automatically cleaned up after the session.
    
    Args:
        patient_id: The ID of the patient.
        file_type: The type of file to retrieve (e.g., "2D image", "CT", "MRI").
        tool_context: The ADK context object for interacting with the user and artifacts.
        
    Returns:
        The path to the temporary file, or an error message if not found.
    """
    patient_id = tool_context.state.get("patient_id", None)
    files = get_patient_file_from_db(patient_id, file_type)
    if not files:
        return f"Error: No '{file_type}' file found for patient {patient_id} in the database."

    # TODO: Assuming only one file of a given type is relevant for analysis at a time
    file_data_blob = files[0]["data"]
    filename = files[0].get("filename", f"patient_{patient_id}_{file_type}")
    mime_type = files[0].get("mime_type", "application/octet-stream")

    # Determine file extension from mime_type or use a generic one
    ext = ".bin"
    if "image/jpeg" in mime_type:
        ext = ".jpg"
    elif "image/png" in mime_type:
        ext = ".png"
    elif "dicom" in mime_type or "application/dicom" in mime_type:
        ext = ".dcm"
    elif "nifti" in mime_type: # Common for .nii or .nii.gz
        ext = ".nii" 
    elif "pdf" in mime_type:
        ext = ".pdf"
        
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    temp_file.write(file_data_blob)
    temp_file.close()
    
    # Store the path for cleanup
    if "temp_files_to_delete" not in tool_context.state:
        tool_context.state["temp_files_to_delete"] = []
    tool_context.state["temp_files_to_delete"].append(temp_file.name)

    logger.info(f"Retrieved '{file_type}' file for patient {patient_id} and saved to temporary path: {temp_file.name}")
    return temp_file.name


def check_emergency_status(triage_output: str, tool_context: ToolContext) -> str:
    """
    Check if triage agent returned emergency abort signal.

    Args:
        triage_output: Output from triage agent to check

    Returns:
        Either "EMERGENCY_DETECTED" or "NO_EMERGENCY"
    """
    if "EMERGENCY_ABORT:" in triage_output:
        emergency_msg = triage_output.split("EMERGENCY_ABORT:")[1].strip()
        tool_context.state["final_diagnosis"] = f"EMERGENCY: {emergency_msg}"
        tool_context.state["is_emergency"] = True
        logger.critical(f"Emergency detected: {emergency_msg}")
        return f"EMERGENCY_DETECTED: {emergency_msg}"
    else:
        return "NO_EMERGENCY"


# ============================================================================
# TOOL EXPORTS
# ============================================================================

__all__ = [
    "load_patient_case",  # NEW: Load patient from database and set state
    "store_patient_data",
    "store_patient_data_multiple",
    "get_patient_summary",
    "update_differential_diagnosis",
    "finalize_diagnosis",
    "increment_diagnostic_loop",
    "check_emergency_status",
    "access_patient_database",
    "get_patient_raw_file_and_path",
    "load_artifacts",
]
