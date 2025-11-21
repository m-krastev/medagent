import asyncio
import logging
from typing import Optional
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from rich.console import Console

from src.domain.models import PatientCase, LabResult, ImagingReport
from src.domain.exceptions.medical import EmergencyAbortException
from src.core.agent_factory import AgentFactory

logger = logging.getLogger(__name__)
console = Console()

class MedicalOrchestrator:
    """
    The Central Nervous System of the application.
    Manages the lifecycle of a PatientCase through the agent swarm.
    """
    
    @staticmethod
    def collect_demographics() -> tuple[int, str]:
        """
        Collect patient demographics via CLI with validation.
        Returns: (age, sex)
        """
        # Collect Age
        while True:
            age_input = console.input("[bold cyan]What age are you?[/bold cyan]: ").strip()
            try:
                age = int(age_input)
                if 0 < age < 200:
                    break
                else:
                    console.print("[bold red]Please enter an integer between 1 and 199.[/bold red]")
            except ValueError:
                console.print("[bold red]Please enter a valid number.[/bold red]")
        
        # Collect Sex
        while True:
            sex_input = console.input("[bold cyan]What is your sex? (m/f)[/bold cyan]: ").strip().lower()
            if sex_input in ["male", "m"]:
                sex = "Male"
                break
            elif sex_input in ["female", "f"]:
                sex = "Female"
                break
            else:
                console.print("[bold red]Please enter 'male', 'female', 'm', or 'f'.[/bold red]")
        
        return age, sex
    
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
            runner = Runner(agent=agent, app_name="agents", session_service=self.session_service)
            
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

    async def run_diagnostic_loop(self, initial_complaint: str = None) -> PatientCase:
        """
        Executes the full diagnostic workflow with interactive information gathering.
        Collects demographics first, then the chief complaint via triage.
        """
        # 1. Initialization - Collect demographics first
        console.print("\n[bold cyan]Patient Information[/bold cyan]\n")
        age, sex = self.collect_demographics()
        
        logger.info(f"Patient: Age: {age}, Sex: {sex}")
        
        # 2. Initialize case with demographics (complaint will be collected via triage)
        case = PatientCase(chief_complaint="", age=age, gender=sex)
        logger.info(f"Starting Case {case.case_id}")
        
        # Create session for the case
        await self.session_service.create_session(session_id=case.case_id, app_name="agents", user_id="system")
        
        try:
            # 3. Triage Phase - Collect and assess chief complaint with clarification loop
            complaint = None
            triage_complete = False
            triage_attempts = 0
            max_triage_attempts = 5
            
            while not triage_complete and triage_attempts < max_triage_attempts:
                triage_attempts += 1
                
                # Get initial complaint or follow-up response
                if not complaint:
                    complaint_input = console.input("[bold cyan]What brings you in today?[/bold cyan] ").strip()
                else:
                    complaint_input = console.input("[bold cyan]Please provide more details:[/bold cyan] ").strip()
                
                if not complaint_input:
                    console.print("[bold red]Please describe your complaint.[/bold red]")
                    continue
                
                # Update complaint with any new information
                if complaint:
                    complaint += f" {complaint_input}"
                else:
                    complaint = complaint_input
                
                case.chief_complaint = complaint
                
                # Assess with triage agent
                triage_out = await self._invoke_agent("triage", f"Assess patient complaint: {complaint}", case)
                
                # Handle Emergency
                if "EMERGENCY_ABORT:" in triage_out:
                    raise EmergencyAbortException(triage_out.split("EMERGENCY_ABORT:")[1].strip())
                
                # Handle Clarification Request
                if "CLARIFY_COMPLAINT:" in triage_out:
                    clarification_q = triage_out.split("CLARIFY_COMPLAINT:")[1].strip()
                    console.print(f"\n🤖 [bold blue]DOCTOR ASKS[/bold blue]: {clarification_q}\n")
                    # Loop continues to ask for more details
                    continue
                
                # Handle Successful Triage
                if "TRIAGE_SUMMARY:" in triage_out:
                    case.history_present_illness = triage_out.split("TRIAGE_SUMMARY:")[1].strip()
                    triage_complete = True
                else:
                    case.history_present_illness = triage_out
                    triage_complete = True
            
            if not triage_complete:
                console.print("[bold yellow]Unable to obtain adequate complaint details. Proceeding with available information.[/bold yellow]")
                logger.warning("Triage did not complete after max attempts. Proceeding anyway.")

            # 3. Hypothesis Generation
            hypo_out = await self._invoke_agent("hypothesis", "Generate Differential Diagnosis.", case)
            case.differential_diagnosis.append(hypo_out)
            
            # 4. The Judge Loop - Continue until user decides to finish
            MAX_LOOPS = 3
            user_finished = False
            
            for i in range(MAX_LOOPS):
                if user_finished:
                    break
                    
                logger.info(f"--- Diagnostic Loop {i+1}/{MAX_LOOPS} ---")
                
                decision = await self._invoke_agent("judge", "Review evidence. Decide next step.", case)
                
                # Check for Finalization from Judge
                if "DIAGNOSIS_FINAL:" in decision:
                    case.final_diagnosis = decision.split("DIAGNOSIS_FINAL:")[1].strip()
                    logger.info("Diagnosis Finalized by Judge.")
                    break
                
                # Dispatch Commands
                await self._dispatch_command(decision, case)
                
                # 4.1 Check if Judge is asking for more patient information
                if "ASK_PATIENT:" in decision:
                    question = decision.split("ASK_PATIENT:")[1].strip()
                    console.print(f"\n🤖 [bold blue]DOCTOR ASKS[/bold blue]: {question}")
                    
                    # await input: provide info or finish
                    choice = None
                    while choice not in ["1", "2"]:
                        console.print("\n[bold cyan]Options:[/bold cyan]")
                        console.print("1. Provide more information")
                        console.print("2. Finish and get diagnosis")
                        
                        choice = console.input("[bold cyan]👤 Your choice (1 or 2)[/bold cyan]: ").strip()
                        
                        if choice not in ["1", "2"]:
                            console.print("[bold red]Invalid choice. Please enter 1 or 2.[/bold red]")
                            choice = None
                    
                    if choice == "1":
                        user_answer = console.input("[bold cyan]👤 PATIENT ANSWER[/bold cyan]: ")
                        if user_answer.strip():
                            case.history_present_illness += f"\n[Interview] Q: {question} A: {user_answer}"
                            logger.info(f"User provided: {user_answer}")
                            # loop continues to next iteration with new data
                        else:
                            # no new data provided, move to final diagnosis
                            console.print("\n[bold yellow]No additional information provided. Generating final diagnosis with current data...[/bold yellow]")
                            logger.info("User chose option 1 but provided no new data. Finalizing diagnosis.")
                            user_finished = True
                    elif choice == "2":
                        console.print("\n[bold yellow]Finishing diagnostic evaluation. Generating final diagnosis...[/bold yellow]")
                        logger.info("User chose to finish. Exiting diagnostic loop.")
                        user_finished = True
                
                # Refine Hypothesis based on new data (if not finished)
                if not user_finished:
                    hypo_update = await self._invoke_agent("hypothesis", "Update Differential based on new evidence.", case)
                    case.differential_diagnosis.append(hypo_update)

            # 5. Final Report - Always generate if no diagnosis yet
            if not case.final_diagnosis:
                # if Judge didn't finalize, use the latest differential as basis for final diagnosis
                logger.info("Generating final diagnosis from accumulated evidence.")
                final_reasoning = await self._invoke_agent("judge", "Based on all evidence gathered, provide your final diagnosis. Start with DIAGNOSIS_FINAL:", case)
                if "DIAGNOSIS_FINAL:" in final_reasoning:
                    case.final_diagnosis = final_reasoning.split("DIAGNOSIS_FINAL:")[1].strip()
                else:
                    case.final_diagnosis = case.differential_diagnosis[-1] if case.differential_diagnosis else "Inconclusive - Referral Required"
            
            if case.final_diagnosis:
                report = await self._invoke_agent("research", f"Write Physician Handoff for: {case.final_diagnosis}", case)
                case.research_notes.append(report)

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
            # ASK_PATIENT is handled in the main loop after _dispatch_command
            # No action needed here
            pass
