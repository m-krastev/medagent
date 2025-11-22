import pytest
from medagent.infrastructure.external.simulators import (
    MRISimulator, 
    tool_analyze_mri,
    MRIReport
)


def test_mri_simulator_initialization():
    """Test MRI simulator can be initialized."""
    mri_sim = MRISimulator()
    assert mri_sim is not None


def test_mri_brain_stroke_analysis():
    """Test MRI analysis for brain stroke."""
    mri_sim = MRISimulator()
    report = mri_sim.analyze_mri_slice("brain", "acute stroke")
    
    assert isinstance(report, MRIReport)
    assert report.region == "brain"
    assert "T1" in report.sequences
    assert "T2" in report.sequences
    assert "FLAIR" in report.sequences
    assert "DWI" in report.sequences
    assert "ischemic" in report.impression.lower() or "stroke" in report.impression.lower()
    assert len(report.findings) > 0


def test_mri_brain_hemorrhage_analysis():
    """Test MRI analysis for brain hemorrhage."""
    mri_sim = MRISimulator()
    report = mri_sim.analyze_mri_slice("brain", "hemorrhage")
    
    assert isinstance(report, MRIReport)
    assert "hemorrhage" in report.impression.lower() or "bleed" in report.impression.lower()


def test_mri_brain_tumor_analysis():
    """Test MRI analysis for brain tumor."""
    mri_sim = MRISimulator()
    report = mri_sim.analyze_mri_slice("brain", "tumor suspected")
    
    assert isinstance(report, MRIReport)
    assert "tumor" in report.impression.lower() or "glioma" in report.impression.lower() or "mass" in report.impression.lower()


def test_mri_brain_ms_analysis():
    """Test MRI analysis for multiple sclerosis."""
    mri_sim = MRISimulator()
    report = mri_sim.analyze_mri_slice("brain", "multiple sclerosis")
    
    assert isinstance(report, MRIReport)
    assert "sclerosis" in report.impression.lower() or "demyelinating" in report.impression.lower()


def test_mri_spine_herniation_analysis():
    """Test MRI analysis for spine disc herniation."""
    mri_sim = MRISimulator()
    report = mri_sim.analyze_mri_slice("spine", "disc herniation")
    
    assert isinstance(report, MRIReport)
    assert report.region == "spine"
    assert "herniation" in report.impression.lower() or "disc" in report.impression.lower()


def test_mri_normal_brain():
    """Test MRI analysis for normal brain."""
    mri_sim = MRISimulator()
    report = mri_sim.analyze_mri_slice("brain", "")
    
    assert isinstance(report, MRIReport)
    assert "normal" in report.impression.lower()


def test_mri_tool_wrapper():
    """Test the tool_analyze_mri wrapper function."""
    result = tool_analyze_mri("brain", "stroke")
    
    assert isinstance(result, str)
    assert "MRI" in result
    assert "brain" in result.lower() or "BRAIN" in result
    assert len(result) > 0


def test_mri_report_string_representation():
    """Test MRI report string formatting."""
    report = MRIReport(
        region="brain",
        sequences=["T1", "T2"],
        findings="Test findings",
        impression="Test impression"
    )
    
    report_str = str(report)
    assert "MRI BRAIN" in report_str
    assert "T1" in report_str
    assert "T2" in report_str
    assert "Test findings" in report_str
    assert "Test impression" in report_str
