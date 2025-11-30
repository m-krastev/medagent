import asyncio
import importlib
import sys
from unittest.mock import MagicMock, patch

import pytest
from google.adk.tools.tool_context import ToolContext # Keep ToolContext for spec in mock

# Global mocks for ADK Agent and AgentTool. These will be reset by the fixture.
MockADKAgent = MagicMock()
MockADKAgentTool = MagicMock()

@pytest.fixture(autouse=True)
def mock_dependencies_for_all_tests():
    """
    Mocks external dependencies for all tests in this module.
    This fixture ensures that mocks are reset for each test to avoid cross-test contamination
    and manages the re-import of `medagent.agent` to ensure mocks are active.
    """
    # Clear module cache for medagent.agent and its sub-agents to force re-import
    # This is crucial because `root_agent` and sub-agents are instantiated at module load time.
    modules_to_clear = [
        'medagent.agent',
        'medagent.sub_agents.triage.agent',
        'medagent.sub_agents.hypothesis.agent',
        'medagent.sub_agents.judge.agent',
        'medagent.sub_agents.evidence.agent',
        'medagent.sub_agents.imaging.agent',
        'medagent.sub_agents.research.agent',
        'medagent.tools', 
        'medagent.config',
        'medagent.prompt',
        'medagent.utils.location',
        'medagent.patient_db_tool',
    ]
    for module_name in modules_to_clear:
        if module_name in sys.modules:
            del sys.modules[module_name]

    # Reset global mocks
    MockADKAgent.reset_mock()
    MockADKAgentTool.reset_mock()

    # Apply patches as context managers within the fixture
    with patch('medagent.agent.Agent', new=MockADKAgent), \
         patch('medagent.agent.AgentTool', new=MockADKAgentTool), \
         patch('medagent.config.settings') as mock_settings, \
         patch('medagent.prompt') as mock_prompt, \
         patch('medagent.utils.location.get_location_from_ip') as mock_get_location, \
         patch('google.adk.tools.load_artifacts') as mock_adk_load_artifacts, \
         patch('medagent.patient_db_tool.get_patient_file_from_db') as mock_get_patient_file_from_db_func, \
         patch('tempfile.NamedTemporaryFile') as mock_temp_file:
        
        # Configure mocks before importing modules that use them
        mock_settings.MODEL_REASONING = "mock-model"
        mock_prompt.MEDICAL_ORCHESTRATOR_INSTRUCTION = "Mock instruction."
        mock_get_location.return_value = "Mock Location"
        mock_adk_load_artifacts.return_value = "Mock ADK Artifact Content"
        
        mock_file_obj = MagicMock()
        mock_file_obj.name = "/tmp/mock_temp_file.txt"
        mock_temp_file.return_value = mock_file_obj

        # --- IMPORTANT: Perform imports *after* patches and mock configurations ---
        _agent_module = importlib.import_module('medagent.agent')
        _tools_module = importlib.import_module('medagent.tools')
        _triage_agent_module = importlib.import_module('medagent.sub_agents.triage.agent')
        _hypothesis_agent_module = importlib.import_module('medagent.sub_agents.hypothesis.agent')
        _judge_agent_module = importlib.import_module('medagent.sub_agents.judge.agent')
        _evidence_agent_module = importlib.import_module('medagent.sub_agents.evidence.agent')
        _imaging_agent_module = importlib.import_module('medagent.sub_agents.imaging.agent')
        _research_agent_module = importlib.import_module('medagent.sub_agents.research.agent')

        # Extract the necessary objects from the re-imported modules
        root_agent = _agent_module.root_agent
        get_patient_raw_file_and_path = _tools_module.get_patient_raw_file_and_path
        store_patient_data = _tools_module.store_patient_data
        
        # For test_root_agent_tools_presence, extract actual tool functions and sub-agent instances
        actual_tools = {
            "store_patient_data": _tools_module.store_patient_data, 
            "get_patient_summary": _tools_module.get_patient_summary, 
            "update_differential_diagnosis": _tools_module.update_differential_diagnosis,
            "finalize_diagnosis": _tools_module.finalize_diagnosis, 
            "increment_diagnostic_loop": _tools_module.increment_diagnostic_loop, 
            "check_emergency_status": _tools_module.check_emergency_status,
            "access_patient_database": _tools_module.access_patient_database, 
            "get_patient_raw_file_and_path": _tools_module.get_patient_raw_file_and_path, 
            "load_artifacts": _tools_module.load_artifacts, # This load_artifacts is from google.adk.tools, but tools module re-exports it
        }
        sub_agents = {
            "triage_agent": _triage_agent_module.triage_agent,
            "hypothesis_agent": _hypothesis_agent_module.hypothesis_agent,
            "judge_agent": _judge_agent_module.judge_agent,
            "evidence_agent": _evidence_agent_module.evidence_agent,
            "imaging_agent": _imaging_agent_module.imaging_agent,
            "research_agent": _research_agent_module.research_agent,
        }

        # Provide reloaded root_agent and mocks to tests
        yield {
            "root_agent": root_agent,
            "MockADKAgent": MockADKAgent,
            "MockADKAgentTool": MockADKAgentTool,
            "get_patient_raw_file_and_path": get_patient_raw_file_and_path,
            "store_patient_data": store_patient_data,
            "mock_get_patient_file_from_db_func": mock_get_patient_file_from_db_func,
            "actual_tools": actual_tools,
            "sub_agents": sub_agents,
        }


@pytest.mark.asyncio
@pytest.mark.parametrize("patient_id, file_type, file_data_blob, expected_temp_file_path", [
    ("MM-2000", "2D image", b"mock image data", "/tmp/mock_temp_file.txt"),
    ("MM-2001", "CT", b"mock ct scan data", "/tmp/mock_temp_file.txt"),
])
async def test_get_patient_raw_file_and_path(patient_id, file_type, file_data_blob, expected_temp_file_path, mock_dependencies_for_all_tests):
    """
    Test get_patient_raw_file_and_path function.
    It retrieves a file from the database, saves it to a temporary file, and returns the path.
    """
    get_patient_raw_file_and_path_func = mock_dependencies_for_all_tests["get_patient_raw_file_and_path"]
    mock_get_patient_file_from_db_func = mock_dependencies_for_all_tests["mock_get_patient_file_from_db_func"]
    
    # Mock ToolContext
    mock_tool_context = MagicMock()
    mock_tool_context.state = {"temp_files_to_delete": []}

    # Use the directly patched mock for get_patient_file_from_db
    with patch('tempfile.NamedTemporaryFile') as mock_temp_file:
        
        # Configure mock_temp_file to return a mock file object
        mock_file_obj = MagicMock()
        mock_file_obj.name = expected_temp_file_path
        mock_temp_file.return_value = mock_file_obj

        mock_get_patient_file_from_db_func.return_value = [
            {"data": file_data_blob, "type": file_type, "filename": f"{patient_id}_{file_type}", "mime_type": "image/jpeg"}
        ]

        # Call the async function
        result_path = await get_patient_raw_file_and_path_func(patient_id, file_type, mock_tool_context)
        
        # Assertions
        mock_get_patient_file_from_db_func.assert_called_once_with(patient_id, file_type)
        mock_temp_file.assert_called_once()
        mock_file_obj.write.assert_called_once_with(file_data_blob)
        mock_file_obj.close.assert_called_once()
        assert result_path == expected_temp_file_path
        assert expected_temp_file_path in mock_tool_context.state["temp_files_to_delete"]


def test_root_agent_initialization(mock_dependencies_for_all_tests):
    """
    Test that the root_agent is initialized correctly with its name, model, description,
    instruction (including location context), and tools.
    """
    MockADKAgent = mock_dependencies_for_all_tests["MockADKAgent"]
    MockADKAgentTool = mock_dependencies_for_all_tests["MockADKAgentTool"]
    root_agent_instance = mock_dependencies_for_all_tests["root_agent"]

    assert MockADKAgent.call_count == 7, f"Expected Agent to be called 7 times, but was called {MockADKAgent.call_count} times."
    
    root_agent_call = None
    for call_args, call_kwargs in MockADKAgent.call_args_list:
        if call_kwargs.get("name") == "medical_orchestrator":
            root_agent_call = (call_args, call_kwargs)
            break
    
    assert root_agent_call is not None, "root_agent (medical_orchestrator) was not initialized."
    
    _, call_kwargs = root_agent_call
    
    assert call_kwargs["name"] == "medical_orchestrator"
    assert call_kwargs["model"] == "mock-model"
    assert "Orchestrates multi-agent medical diagnostic workflow" in call_kwargs["description"]
    assert "LOCATION CONTEXT: The current user is located in Mock Location." in call_kwargs["instruction"]
    
    assert len(call_kwargs["tools"]) > 0
    
    assert MockADKAgentTool.call_count == 6, f"Expected AgentTool to be called 6 times for sub-agents, but was called {MockADKAgentTool.call_count} times."


def test_root_agent_tools_presence(mock_dependencies_for_all_tests):
    """
    Verifies that specific expected tools are present in the root_agent's tool list
    and that AgentTool is called correctly for sub-agents.
    """
    MockADKAgent = mock_dependencies_for_all_tests["MockADKAgent"]
    MockADKAgentTool = mock_dependencies_for_all_tests["MockADKAgentTool"]
    actual_tools = mock_dependencies_for_all_tests["actual_tools"]
    sub_agents = mock_dependencies_for_all_tests["sub_agents"]

    root_agent_call_kwargs = None
    for call_args, call_kwargs in MockADKAgent.call_args_list:
        if call_kwargs.get("name") == "medical_orchestrator":
            root_agent_call_kwargs = call_kwargs
            break
    
    assert root_agent_call_kwargs is not None, "root_agent (medical_orchestrator) was not initialized."
    
    tools_list = root_agent_call_kwargs["tools"]

    expected_direct_tools = [
        actual_tools["store_patient_data"], actual_tools["get_patient_summary"], actual_tools["update_differential_diagnosis"],
        actual_tools["finalize_diagnosis"], actual_tools["increment_diagnostic_loop"], actual_tools["check_emergency_status"],
        actual_tools["access_patient_database"], actual_tools["get_patient_raw_file_and_path"], actual_tools["load_artifacts"]
    ]

    expected_sub_agents_list = [
        sub_agents["triage_agent"], sub_agents["hypothesis_agent"], sub_agents["judge_agent"],
        sub_agents["evidence_agent"], sub_agents["imaging_agent"], sub_agents["research_agent"]
    ]

    # Verify direct tools are in the list
    for tool in expected_direct_tools:
        assert tool in tools_list, f"Tool {tool.__name__} not found in root_agent tools."

    assert MockADKAgentTool.call_count == len(expected_sub_agents_list), "Incorrect number of AgentTools created."

    called_agents = [call.kwargs['agent'] for call in MockADKAgentTool.call_args_list]
    for sub_agent in expected_sub_agents_list:
        assert sub_agent in called_agents, f"Sub-agent {sub_agent.name} not passed to AgentTool."

def test_store_patient_data_adds_to_context(mock_dependencies_for_all_tests):
    """
    Tests that store_patient_data correctly adds data to the tool_context's state.
    This simulates adding to the agent's context.
    """
    store_patient_data_func = mock_dependencies_for_all_tests["store_patient_data"]
    
    mock_tool_context = MagicMock(spec=ToolContext)
    mock_tool_context.state = {}

    field_name = "patient_age"
    field_value = 45
    
    result = store_patient_data_func(field_name, field_value, mock_tool_context)
    
    assert result == f"Successfully stored {field_name} in patient record"
    assert mock_tool_context.state[field_name] == field_value
    assert mock_tool_context.state.get("patient_age") == 45
    assert len(mock_tool_context.state) == 1
