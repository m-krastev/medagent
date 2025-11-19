import pytest
from src.domain.models import PatientCase, Vitals, LabResult

def test_vitals_validation():
    """Ensure Pydantic validation works for Vitals."""
    v = Vitals(hr=80, bp_systolic=120)
    assert v.is_stable is True
    
    v_unstable = Vitals(hr=150)
    assert v_unstable.is_stable is False

def test_case_initialization():
    case = PatientCase(chief_complaint="Pain")
    assert case.case_id is not None
    assert len(case.lab_results) == 0

def test_clinical_summary():
    case = PatientCase(chief_complaint="Cough", age=50, gender="Male")
    summary = case.clinical_summary()
    assert "50yo Male" in summary
    assert "Cough" in summary
