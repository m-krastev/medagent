from typing import Dict
from google.adk.agents import LlmAgent
from ..agents.registry import (
    create_triage_agent, create_hypothesis_agent, create_judge_agent,
    create_evidence_agent, create_imaging_agent, create_research_agent,
    create_pathology_agent, create_radiology_agent, create_neurology_agent
)

class AgentFactory:
    """
    Factory class to create and manage agent instances.
    """
    @staticmethod
    def create_agents() -> Dict[str, LlmAgent]:
        return {
            "triage": create_triage_agent(),
            "hypothesis": create_hypothesis_agent(),
            "judge": create_judge_agent(),
            "evidence": create_evidence_agent(),
            "imaging": create_imaging_agent(),
            "research": create_research_agent(),
            "pathology": create_pathology_agent(),
            "radiology": create_radiology_agent(),
            "neurology": create_neurology_agent()
        }
