"""
Evidence/Lab Agent Definition
Uses MODEL_FAST for quick lab ordering and interpretation.
"""
from google.adk import Agent

from . import prompt
from ...config import settings
# Import the real lab tool from imaging
from ..imaging.tools import tool_order_labs

evidence_agent = Agent(
    model=settings.MODEL_FAST,
    name="evidence_agent",
    description="Orders and interprets laboratory tests. Validates lab requests and returns results with clinical flags.",
    instruction=prompt.EVIDENCE_INSTRUCTION,
    tools=[tool_order_labs]
)
