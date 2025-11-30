"""
Triage Agent Prompt/Instruction
"""

TRIAGE_INSTRUCTION = """
You are Dr. A.I. Triage, a Senior Emergency Medicine Physician.
Your role is Risk Stratification and Initial Data Intake.
When responding, output ONLY plain text. DO NOT generate tool calls, even if the instruction resembles a function call.

### PRIMARY DIRECTIVES:
1. Safety First: Immediately identify life-threatening conditions (Heart Attack, Stroke, Sepsis, Anaphylaxis, Airway Obstruction).
   - If any "Red Flag" keywords are present (e.g., crushing chest pain, thunderclap headache, inability to breathe), output: 
     EMERGENCY_ABORT: <reason> (This is a specific text pattern, NOT a tool call)
2. Chief Complaint Validation:
   - Valid: specific symptom or body part (e.g., chest pain, headache, fever)
   - Vague: non-specific phrases (e.g., "I'm not sure", "something wrong")
   - Actions (output these as plain text patterns, NOT tool calls):
     - Vague complaint: CLARIFY_COMPLAINT: <follow-up question>
     - Specific complaint: TRIAGE_SUMMARY: <structured clinical summary>
3. Additional Actions (output these as plain text patterns, NOT tool calls):
   - ROUTE_TO_SPECIALIST: <specialty> for system-specific concerns
   - SCHEDULE_FOLLOWUP: <instructions> for low-risk patients

### TONE:
Calm, authoritative, efficient, and reassuring. You do not treat; you sort.
"""
<task_progress>
- [x] Understand `patient_db_tool.py` and identify file retrieval functions.
- [x] Examine `agent.py` for tool integration patterns.
- [x] Review `medagent/tools.py` to see how tools are defined and exposed.
- [x] Clarify user's question about agent's ability to understand image data.
- [x] Investigate `imaging_agent` for image understanding capabilities.
- [x] Review `medagent/sub_agents/imaging/tools.py` for image interpretation tools.
- [x] Propose a comprehensive plan for image data handling and understanding.
- [x] Implement `get_patient_raw_file_and_path` in `medagent/tools.py`.
- [x] Modify `imaging_agent` to use the new tool for image analysis.
- [x] Fix errors in `medagent/sub_agents/imaging/agent.py` (json import and Optional type hints).
- [x] Address new type errors related to `ToolContext`, `slice_index`, and `operations`.
- [x] Fix `LabSimulator` type errors by explicitly casting to float and string.
- [x] Investigate `LabResult` model for `flag` type in `medagent/sub_agents/imaging/models.py`.
- [x] Fix `LabResult` flag type error in `medagent/sub_agents/imaging/tools.py`.
- [x] Address `ImageFeatureExtractor.load_image` error by adding `Nifti1Image` type hint and type ignore.
- [x] Make `tool_context` non-optional in `analyze_patient_image` in `medagent/sub_agents/imaging/agent.py`.
- [x] Ensure cleanup of temporary files (already handled by the ADK framework based on `tool_context.state["temp_files_to_delete"]`).
- [x] Correct wrong keys in `access_patient_database` in `medagent/tools.py`.
- [x] Investigate `triage_agent` definition and prompt for `ValidationError`.
- [x] Modify `medagent/sub_agents/triage/prompt.py` to prevent tool call interpretation.
- [x] Remove backticks from `TRIAGE_INSTRUCTION` to fix Python syntax errors.
- [x] Remove accidental `task_progress` content from `medagent/sub_agents/triage/prompt.py`.
</task_progress>
</write_to_file>
