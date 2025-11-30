"""
Imaging Agent Definition
Uses MODEL_FAST for quick imaging ordering and interpretation.
"""
import json # Import json for json.dumps
from typing import Optional # Import Optional for type hints

from google.adk import Agent
from google.adk.tools.tool_context import ToolContext

from . import prompt
from . import tools
from ...config import settings
from ...tools import get_patient_raw_file_and_path # Import the new tool

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_patient_image(
    patient_id: str,
    file_type: str,
    tool_context: ToolContext, # Make tool_context non-optional
    slice_index: Optional[int] = None,
    operations: Optional[list[str]] = None,
    bins: int = 64,
) -> str:
    """
    [TOOL] Retrieves a patient's raw image file, saves it temporarily,
    analyzes it for features, and returns the analysis results.

    Args:
        patient_id: The ID of the patient.
        file_type: The type of image file (e.g., "CT", "MRI", "2D image").
        slice_index: Specific slice index for 3D images.
        operations: List of analysis operations to perform (e.g., "histogram", "edges", "contrast").
        bins: Number of bins for histogram analysis.
        tool_context: ADK tool context for accessing session state.

    Returns:
        A JSON string of the analysis results or an error message.
    """
    # 1. Retrieve the raw file and get its temporary path
    temp_file_path: str = await get_patient_raw_file_and_path(patient_id, file_type, tool_context)
    logging.info(f"Temporary file path for analysis: {temp_file_path}")

    if temp_file_path.startswith("Error:"):
        return temp_file_path # Return error if file retrieval failed

    # 2. Analyze the image using the imaging_tools's tool_analyze_image
    try:
        analysis_results = tools.tool_analyze_image(
            path=temp_file_path,
            slice_index=slice_index,
            operations=operations,
            bins=bins,
            tool_context=tool_context,
        )
        # Ensure analysis_results is a non-empty dictionary before JSON serialization
        if not analysis_results:
            analysis_results = {"status": "warning", "message": "Image analysis returned no results or an empty dictionary."}
        return json.dumps(analysis_results, indent=2)
    except Exception as e:
        return f"Error analyzing image at {temp_file_path}: {e}"
    finally:
        # Cleanup is handled by the ADK framework for temp_files_to_delete in tool_context state
        pass


imaging_agent = Agent(
    model=settings.MODEL_FAST,
    name="imaging_agent",
    description="Orders and interprets radiology studies (CT, MRI, X-ray, Ultrasound). Generates structured reports with findings and impressions, and can analyze raw image data.",
    instruction=prompt.IMAGING_INSTRUCTION,
    tools=[
        tools.tool_order_imaging,
        analyze_patient_image, # Add the new image analysis tool
    ]
)
