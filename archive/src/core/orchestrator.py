import asyncio
import logging
from typing import Optional
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from src.domain.models import PatientCase, LabResult, ImagingReport
from src.domain.exceptions.medical import EmergencyAbortException
from src.core.agent_factory import AgentFactory

logger = logging.getLogger(__name__)

class MedicalOrchestrator:
    """
    The Central Nervous System of the application.
    Manages the lifecycle of a PatientCase through the agent swarm.
    """
    
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.agents = AgentFactory.create_agents()

    async def _invoke_agent(self, agent_name: str, task: str, case: PatientCase) -> str:
        """
        Helper to run a specific agent with the current case context.
        """
        logger.info(f"Invoking Agent: {agent_name.upper()}")
        try:
            agent = self.agents[agent_name]
            
            # Construct Contextual Prompt
            context = f"CURRENT CASE STATE:\n{case.clinical_summary()}\n\nTASK:\n{task}"
            msg = types.Content(parts=[types.Part(text=context)])
            
            response_text = ""
            # Use the case_id as session_id to maintain thread continuity per patient
            async for event in runner.run_async(user_id="system", session_id=case.case_id, new_message=msg):
                if event.is_final_response() and event.content:
                    response_text = event.content.parts[0].text
            
            if not response_text:
                logger.warning(f"Agent {agent_name} returned empty response.")
                return "ERROR: No response from agent."

            # Audit Log
            case.add_log(agent_name, response_text)
            logger.info(f"Agent {agent_name} finished.")
            return response_text

        except Exception as e:
            logger.error(f"Error invoking agent {agent_name}: {e}", exc_info=True)
            return f"SYSTEM ERROR: {str(e)}"

    async def run_diagnostic_loop(self, initial_complaint: str) -> PatientCase:
        """
        Executes the full diagnostic workflow.
        """
        # 1. Initialization
        case = PatientCase(chief_complaint=initial_complaint)
        logger.info(f"Starting Case {case.case_id}: {initial_complaint}")
        
        # Create session for the case
        await self.session_service.create_session(session_id=case.case_id, app_name="agents", user_id="system")
        
        try:
            # 2. Triage Phase
            triage_out = await self._invoke_agent("triage", f"Intake patient with complaint: {initial_complaint}", case)
            
            if "EMERGENCY_ABORT" in triage_out:
                raise EmergencyAbortException(triage_out)
            
            # Parse Triage (Simplified for demo - ideally structured output parsing)
            case.history_present_illness = triage_out
            # Assume Triage extracted age/gender or set defaults
            if not case.age: case.age = 45
            if not case.gender: case.gender = "Unknown"

            # 3. Hypothesis Generation
            hypo_out = await self._invoke_agent("hypothesis", "Generate Differential Diagnosis.", case)
            case.differential_diagnosis.append(hypo_out)
            
            # 4. The Judge Loop (Max 5 turns)
            MAX_LOOPS = 5
            for i in range(MAX_LOOPS):
                logger.info(f"--- Diagnostic Loop {i+1}/{MAX_LOOPS} ---")
                
                decision = await self._invoke_agent("judge", "Review evidence. Decide next step.", case)
                
                # Check for Finalization
                if "DIAGNOSIS_FINAL:" in decision:
                    case.final_diagnosis = decision.split("DIAGNOSIS_FINAL:")[1].strip()
                    logger.info("Diagnosis Finalized.")
                    break
                
                # Dispatch Commands
                await self._dispatch_command(decision, case)
                
                # Refine Hypothesis based on new data
                if i < MAX_LOOPS - 1:
                    hypo_update = await self._invoke_agent("hypothesis", "Update Differential based on new evidence.", case)
                    case.differential_diagnosis.append(hypo_update)

            # 5. Final Report
            if case.final_diagnosis:
                report = await self._invoke_agent("research", f"Write Physician Handoff for: {case.final_diagnosis}", case)
                case.research_notes.append(report)
            else:
                case.final_diagnosis = "Inconclusive - Referral Required"

        except EmergencyAbortException as e:
            logger.critical(str(e))
            case.final_diagnosis = str(e)
            
        return case

    async def _dispatch_command(self, decision: str, case: PatientCase):
        """Parses Judge output and routes to specialists."""
        
        if "ORDER_LAB:" in decision:
            test = decision.split("ORDER_LAB:")[1].strip()
            # Infer context from current hypothesis for simulation accuracy
            ctx = str(case.differential_diagnosis[-1]) if case.differential_diagnosis else ""
            res = await self._invoke_agent("evidence", f"Order {test} with context='{ctx}'", case)
            # In a real app, we would parse 'res' into a LabResult object here
            # For now, we append the text to the log which is part of the context
            case.add_log("system", f"Lab Result Received: {res}")
            
        elif "ORDER_IMAGING:" in decision:
            req = decision.split("ORDER_IMAGING:")[1].strip()
            ctx = str(case.differential_diagnosis[-1]) if case.differential_diagnosis else ""
            res = await self._invoke_agent("imaging", f"Order {req} with context='{ctx}'", case)
            case.add_log("system", f"Imaging Report Received: {res}")
            
        elif "CONSULT_LITERATURE:" in decision:
            query = decision.split("CONSULT_LITERATURE:")[1].strip()
            res = await self._invoke_agent("research", query, case)
            case.add_log("system", f"Research Finding: {res}")
            
        elif "ASK_PATIENT:" in decision:
            q = decision.split("ASK_PATIENT:")[1].strip()
            print(f"\n🤖 DOCTOR ASKS: {q}")
            # Simulating user input for automated flow
            # user_ans = input("👤 PATIENT ANSWER: ")
            user_ans = "It started about 2 days ago." 
            case.history_present_illness += f"\n[Interview] Q: {q} A: {user_ans}"
