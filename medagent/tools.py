"""
Tools for Medical Orchestrator Root Agent
State management and workflow coordination tools for the diagnostic process.
"""
import logging
from typing import Optional, Any
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

# ============================================================================
# STATE MANAGEMENT TOOLS
# ============================================================================

def store_patient_data(
    field: str,
    value: Any,
    tool_context: ToolContext
) -> str:
    """
    Store any patient data field in session state.
    
    Args:
        field: Field name (e.g., 'patient_age', 'patient_sex', 'chief_complaint', 'location')
        value: Value to store (can be string, int, dict, list, etc.)
    
    Returns:
        Confirmation message
    """
    tool_context.state[field] = value
    logger.info(f"Stored {field}: {str(value)[:100]}...")
    return f"Successfully stored {field} in patient record"


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
{hpi if hpi else 'Not yet documented'}

VITALS:
{vitals if vitals else 'Not recorded'}

LABORATORY RESULTS:
{labs if labs else 'None ordered'}

IMAGING STUDIES:
{imaging if imaging else 'None ordered'}

DIFFERENTIAL DIAGNOSIS:
{chr(10).join(f'- {d}' for d in ddx) if ddx else 'Not yet formulated'}

FINAL DIAGNOSIS:
{final_dx if final_dx else 'Pending'}
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
    "store_patient_data",
    "get_patient_summary",
    "update_differential_diagnosis",
    "finalize_diagnosis",
    "increment_diagnostic_loop",
    "check_emergency_status",
]
