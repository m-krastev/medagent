"""
Hypothesis/Differential Diagnosis Agent Definition
Uses MODEL_REASONING for complex diagnostic reasoning.
"""
from google.adk import Agent

from . import prompt
from ...config import settings

hypothesis_agent = Agent(
    model=settings.MODEL_REASONING,
    name="hypothesis_agent",
    description="Generates and updates differential diagnoses based on clinical features. Applies medical reasoning frameworks like VINDICATE.",
    instruction=prompt.HYPOTHESIS_INSTRUCTION
)
