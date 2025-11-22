import pytest
import os


def test_pathology_prompt_exists():
    """Ensure pathology prompt is defined."""
    from medagent.config.prompts import PATHOLOGY_PROMPT
    
    assert PATHOLOGY_PROMPT is not None
    assert "Pathologist" in PATHOLOGY_PROMPT
    assert "Laboratory Medicine" in PATHOLOGY_PROMPT


def test_radiology_prompt_exists():
    """Ensure radiology prompt is defined."""
    from medagent.config.prompts import RADIOLOGY_PROMPT
    
    assert RADIOLOGY_PROMPT is not None
    assert "Radiologist" in RADIOLOGY_PROMPT
    assert "MRI" in RADIOLOGY_PROMPT


def test_neurology_prompt_exists():
    """Ensure neurology prompt is defined."""
    from medagent.config.prompts import NEUROLOGY_PROMPT
    
    assert NEUROLOGY_PROMPT is not None
    assert "Neurologist" in NEUROLOGY_PROMPT
    assert "neurological" in NEUROLOGY_PROMPT.lower()


def test_judge_prompt_mentions_specialists():
    """Ensure the judge prompt mentions specialist consultations."""
    from medagent.config.prompts import JUDGE_PROMPT
    
    assert "CONSULT_PATHOLOGY" in JUDGE_PROMPT
    assert "CONSULT_RADIOLOGY" in JUDGE_PROMPT
    assert "CONSULT_NEUROLOGY" in JUDGE_PROMPT
    assert "ANALYZE_MRI" in JUDGE_PROMPT
