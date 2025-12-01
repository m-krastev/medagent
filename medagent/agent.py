"""
Medical Orchestrator Root Agent Definition
ADK-compatible agent that orchestrates the diagnostic workflow.
"""
from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool

from . import prompt
from .config import settings
from .sub_agents.triage.agent import triage_agent
from .sub_agents.hypothesis.agent import hypothesis_agent
from .sub_agents.judge.agent import judge_agent
from .sub_agents.evidence.agent import evidence_agent
from .sub_agents.imaging.agent import imaging_agent
from .sub_agents.research.agent import research_agent
from .tools import (
    load_patient_case,
    store_patient_data,
    store_patient_data_multiple,
    get_patient_summary,
    update_differential_diagnosis,
    finalize_diagnosis,
    increment_diagnostic_loop,
    check_emergency_status,
    access_patient_database,
    get_patient_raw_file_and_path,
    load_artifacts
)
from .utils.location import get_location_from_ip

# Create Root Agent with reasoning model
root_agent = Agent(
    name="medical_orchestrator",
    model=settings.MODEL_REASONING,
    description="Orchestrates multi-agent medical diagnostic workflow through systematic patient assessment, evidence gathering, and clinical reasoning.",
    # NOTE: The automatic location context injection below will not work properly if deployed, this is just for local testing purposes.
    instruction=prompt.MEDICAL_ORCHESTRATOR_INSTRUCTION + f"\n\n LOCATION CONTEXT: The current user is located in {get_location_from_ip()}.",
    tools=[
        # Patient case loading (MUST be called first when working with database cases)
        load_patient_case,
        # Patient data management tools
        store_patient_data,
        store_patient_data_multiple,
        get_patient_summary,
        update_differential_diagnosis,
        finalize_diagnosis,
        increment_diagnostic_loop,
        check_emergency_status,
        access_patient_database,
        get_patient_raw_file_and_path,
        load_artifacts,
        # Sub-agent delegation tools
        AgentTool(agent=triage_agent),
        AgentTool(agent=hypothesis_agent),
        AgentTool(agent=judge_agent),
        AgentTool(agent=evidence_agent),
        AgentTool(agent=imaging_agent),
        AgentTool(agent=research_agent),
    ]
)

__all__ = ["root_agent"]
