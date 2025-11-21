from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from config.settings import settings
import google.generativeai as genai

# Configure the Google GenAI library with the API key from settings
genai.configure(api_key=settings.GOOGLE_API_KEY)

from config.prompts import (
    TRIAGE_PROMPT, HYPOTHESIS_PROMPT, JUDGE_PROMPT,
    EVIDENCE_PROMPT, IMAGING_PROMPT, RESEARCH_PROMPT
)
from src.infrastructure.external.simulators import tool_order_labs, tool_order_imaging
from src.infrastructure.rag.engine import tool_consult_guidelines

def create_triage_agent() -> LlmAgent:
    return LlmAgent(
        model=Gemini(model_name=settings.MODEL_FAST, retry_options=settings.retry_options),
        name="triage_agent",
        instruction=TRIAGE_PROMPT
    )

def create_hypothesis_agent() -> LlmAgent:
    return LlmAgent(
        model=Gemini(model_name=settings.MODEL_REASONING, retry_options=settings.retry_options),
        name="hypothesis_agent",
        instruction=HYPOTHESIS_PROMPT
    )

def create_judge_agent() -> LlmAgent:
    return LlmAgent(
        model=Gemini(model_name=settings.MODEL_REASONING, retry_options=settings.retry_options),
        name="judge_agent",
        instruction=JUDGE_PROMPT
    )

def create_evidence_agent() -> LlmAgent:
    return LlmAgent(
        model=Gemini(model_name=settings.MODEL_FAST, retry_options=settings.retry_options),
        name="evidence_agent",
        instruction=EVIDENCE_PROMPT,
        tools=[tool_order_labs]
    )

def create_imaging_agent() -> LlmAgent:
    return LlmAgent(
        model=Gemini(model_name=settings.MODEL_FAST, retry_options=settings.retry_options),
        name="imaging_agent",
        instruction=IMAGING_PROMPT,
        tools=[tool_order_imaging]
    )

def create_research_agent() -> LlmAgent:
    return LlmAgent(
        model=Gemini(model_name=settings.MODEL_REASONING, retry_options=settings.retry_options),
        name="research_agent",
        instruction=RESEARCH_PROMPT
    )
