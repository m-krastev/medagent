"""
Imaging Agent Definition
Uses MODEL_FAST for quick imaging ordering and interpretation.
"""
from google.adk import Agent

from . import prompt
from . import tools
from ...config import settings

imaging_agent = Agent(
    model=settings.MODEL_FAST,
    name="imaging_agent",
    description="Orders and interprets radiology studies (CT, MRI, X-ray, Ultrasound). Generates structured reports with findings and impressions.",
    instruction=prompt.IMAGING_INSTRUCTION,
    tools=[tools.tool_order_imaging]
)
