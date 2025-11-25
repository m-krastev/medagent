"""
Triage Agent Definition
Uses MODEL_FAST for quick initial assessment.
"""
from google.adk import Agent

from . import prompt
from ...config import settings

triage_agent = Agent(
    model=settings.MODEL_FAST,
    name="triage_agent",
    description="Performs initial patient assessment, risk stratification, and chief complaint validation. Identifies life-threatening conditions.",
    instruction=prompt.TRIAGE_INSTRUCTION
)
