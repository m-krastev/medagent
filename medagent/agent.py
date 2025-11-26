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
    store_patient_data,
    get_patient_summary,
    update_differential_diagnosis,
    finalize_diagnosis,
    increment_diagnostic_loop,
    check_emergency_status,
)

# Create Root Agent with reasoning model
root_agent = Agent(
    name="medical_orchestrator",
    model=settings.MODEL_REASONING,
    description="Orchestrates multi-agent medical diagnostic workflow through systematic patient assessment, evidence gathering, and clinical reasoning.",
    instruction=prompt.MEDICAL_ORCHESTRATOR_INSTRUCTION,
    tools=[
        # Patient data management tools
        store_patient_data,
        get_patient_summary,
        update_differential_diagnosis,
        finalize_diagnosis,
        increment_diagnostic_loop,
        check_emergency_status,
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
