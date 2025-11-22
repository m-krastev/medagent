class MedicalSystemException(Exception):
    """Base exception for the medical system."""
    pass

class EmergencyAbortException(MedicalSystemException):
    """Raised when Triage detects a life-threatening condition."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"EMERGENCY PROTOCOL ACTIVATED: {reason}")

class DataIngestionError(MedicalSystemException):
    """Raised when RAG data loading fails."""
    pass

class InvalidActionError(MedicalSystemException):
    """Raised when an agent outputs a malformed command."""
    pass
