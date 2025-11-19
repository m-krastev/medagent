from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal, Dict
from datetime import datetime
import uuid

# --- Value Objects ---

class Vitals(BaseModel):
    bp_systolic: Optional[int] = Field(None, ge=0, le=300)
    bp_diastolic: Optional[int] = Field(None, ge=0, le=200)
    hr: Optional[int] = Field(None, ge=0, le=300)
    temp_c: Optional[float] = Field(None, ge=20.0, le=45.0)
    spo2: Optional[float] = Field(None, ge=0.0, le=100.0)
    resp_rate: Optional[int] = Field(None, ge=0, le=100)

    @property
    def is_stable(self) -> bool:
        if self.hr and (self.hr > 120 or self.hr < 40): return False
        if self.spo2 and self.spo2 < 90: return False
        if self.bp_systolic and self.bp_systolic < 90: return False
        return True

class LabResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_name: str
    value: float
    unit: str
    reference_range: str
    flag: Literal["NORMAL", "HIGH", "LOW", "CRITICAL"]
    timestamp: datetime = Field(default_factory=datetime.now)

    def __str__(self):
        return f"{self.test_name}: {self.value} {self.unit} [{self.flag}]"

class ImagingReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    modality: str
    region: str
    findings: str
    impression: str
    timestamp: datetime = Field(default_factory=datetime.now)

# --- Aggregate Roots ---

class PatientCase(BaseModel):
    """
    The Aggregate Root representing the entire diagnostic session.
    This object is passed between agents and maintains the Single Source of Truth.
    """
    case_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Demographics
    age: Optional[int] = None
    gender: Optional[str] = None
    
    # Clinical Data
    chief_complaint: str
    history_present_illness: str = ""
    past_medical_history: List[str] = []
    
    # Objective Data
    vitals: Vitals = Field(default_factory=Vitals)
    lab_results: List[LabResult] = []
    imaging_reports: List[ImagingReport] = []
    
    # Reasoning State
    differential_diagnosis: List[str] = []
    research_notes: List[str] = []
    final_diagnosis: Optional[str] = None
    
    # Audit Trail
    action_log: List[str] = []

    def add_log(self, agent: str, action: str):
        entry = f"[{datetime.now().isoformat()}] {agent.upper()}: {action}"
        self.action_log.append(entry)

    def clinical_summary(self) -> str:
        """Generates a dense text summary for LLM context injection."""
        labs = "\n".join([str(l) for l in self.lab_results]) or "None"
        imgs = "\n".join([f"{i.modality} {i.region}: {i.impression}" for i in self.imaging_reports]) or "None"
        
        return (
            f"--- PATIENT SUMMARY ---\n"
            f"ID: {self.case_id}\n"
            f"DEMOGRAPHICS: {self.age}yo {self.gender}\n"
            f"CHIEF COMPLAINT: {self.chief_complaint}\n"
            f"HPI: {self.history_present_illness}\n"
            f"VITALS: {self.vitals.model_dump(exclude_none=True)}\n"
            f"--- OBJECTIVE DATA ---\n"
            f"LABS:\n{labs}\n"
            f"IMAGING:\n{imgs}\n"
            f"--- CURRENT THINKING ---\n"
            f"DIFFERENTIAL: {self.differential_diagnosis}\n"
        )
