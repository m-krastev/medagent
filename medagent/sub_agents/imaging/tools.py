"""
Imaging Agent Tools - Radiology ordering and simulation
"""
from src.medagent.infrastructure.external.simulators import img_sim
from src.medagent.infrastructure.external.simulators import img_feat_extractor
from google.adk.tools.tool_context import ToolContext

def tool_order_imaging(modality: str, region: str, clinical_context: str = "", tool_context: ToolContext = None) -> str:
    """
    [TOOL] Orders a radiology study.
    
    Args:
        modality: CT, MRI, XRAY, US.
        region: Body part (Chest, Head, Abdomen).
        clinical_context: The suspected condition.
        tool_context: ADK tool context for accessing session state.
    
    Returns:
        Radiology report with REPORT ID, FINDINGS, and IMPRESSION.
    """
    # If clinical_context not provided, try to get from state
    if not clinical_context and tool_context:
        differential = tool_context.state.get('temp:differential_diagnosis', [])
        if differential:
            clinical_context = str(differential[-1]) if isinstance(differential, list) else str(differential)
    
    report = img_sim.order_scan(modality, region, clinical_context)
    
    # Store result in state if tool_context available
    if tool_context:
        imaging_reports = tool_context.state.get('temp:imaging_reports', [])
        imaging_reports.append(report.model_dump())
        tool_context.state['temp:imaging_reports'] = imaging_reports
    
    return f"REPORT ID: {report.id}\nFINDINGS: {report.findings}\nIMPRESSION: {report.impression}"

def tool_analyze_image(path: str, slice_index: int = None, operations=None, bins: int = 64, tool_context: ToolContext = None):
    """
    [TOOL] Analyzes a medical image and extracts features.
    
    Args:
        path: File path to the medical image.
        slice_index: Specific slice index for 3D images.
        operations: List of analysis operations to perform.
        bins: Number of bins for histogram analysis.
        tool_context: ADK tool context for accessing session state.
    Returns:
        Dictionary of extracted image features. 
    """
    results = img_feat_extractor.analyze(path, slice_index, operations, bins)
    
    if tool_context:
        image_analyses = tool_context.state.get('temp:image_analyses', [])
        image_analyses.append({'path': path, 'results': results})
        tool_context.state['temp:image_analyses'] = image_analyses
    
    return results
