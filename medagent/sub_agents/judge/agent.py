"""
Judge Agent Definition - Chief Medical Officer
Coordinates diagnostic workflow by evaluating evidence and making strategic decisions.
"""
from google.adk import Agent

from . import prompt
from ...config import settings

# Create Judge Agent with reasoning model (no tools - makes decisions)
judge_agent = Agent(
    model=settings.MODEL_REASONING,
    name="judge_agent",
    description="Chief Medical Officer who evaluates evidence and coordinates diagnostic decisions: ORDER_LAB, ORDER_IMAGING, CONSULT_LITERATURE, ASK_PATIENT, or DIAGNOSIS_FINAL",
    instruction=prompt.JUDGE_INSTRUCTION,
)

__all__ = ["judge_agent"]
