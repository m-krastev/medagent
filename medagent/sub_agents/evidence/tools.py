"""
Evidence Agent Tools - Lab ordering and simulation
"""
from src.medagent.infrastructure.external.simulators import lab_sim
from google.adk.tools.tool_context import ToolContext

def tool_order_labs(test_name: str, clinical_context: str = "", tool_context: ToolContext = None) -> str:
    """
    [TOOL] Orders a specific lab test.
    
    Args:
        test_name: The standard code/name of the test (e.g., WBC, TROPONIN).
        clinical_context: The suspected condition (e.g., 'infection', 'chest pain').
        tool_context: ADK tool context for accessing session state.
    
    Returns:
        Lab result string with test name, value, unit, and flag status.
    """
    # If clinical_context not provided, try to get from state
    if not clinical_context and tool_context:
        # Get current differential diagnosis from state as context
        differential = tool_context.state.get('temp:differential_diagnosis', [])
        if differential:
            clinical_context = str(differential[-1]) if isinstance(differential, list) else str(differential)
    
    result = lab_sim.order_test(test_name, clinical_context)
    
    # Store result in state if tool_context available
    if tool_context:
        lab_results = tool_context.state.get('temp:lab_results', [])
        lab_results.append(result.model_dump())
        tool_context.state['temp:lab_results'] = lab_results
    
    return str(result)
