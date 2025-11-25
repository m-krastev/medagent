"""
Research Agent Definition
Uses MODEL_REASONING for complex literature analysis and report generation.
"""
from google.adk import Agent

from . import prompt
from . import tools
from ...config import settings

research_agent = Agent(
    model=settings.MODEL_REASONING,
    name="research_agent",
    description="Consults medical literature and clinical guidelines. Generates comprehensive physician handoff reports with treatment recommendations.",
    instruction=prompt.RESEARCH_INSTRUCTION,
    tools=[tools.tool_consult_guidelines]
)
