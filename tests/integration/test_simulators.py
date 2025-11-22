from medagent.infrastructure.external.simulators import tool_order_labs, tool_order_imaging

def test_lab_simulator_logic():
    # Test Infection logic
    res_inf = tool_order_labs("WBC", "infection")
    assert "HIGH" in res_inf or "CRITICAL" in res_inf
    
    # Test Normal logic
    res_norm = tool_order_labs("WBC", "healthy")
    assert "NORMAL" in res_norm

def test_imaging_simulator_logic():
    res = tool_order_imaging("CT", "Chest", "pneumonia")
    assert "Pneumonia" in res
