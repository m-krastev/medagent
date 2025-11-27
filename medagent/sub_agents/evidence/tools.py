"""
Evidence Agent Tools - Lab ordering and simulation
"""
from google.adk.tools.tool_context import ToolContext
from google.adk.plugins.save_files_as_artifacts_plugin import SaveFilesAsArtifactsPlugin
import pandas as pd
from ...utils import extract_data 

mimic = extract_data.mimic

# LAB_REFERENCE_RANGES = {
#     "WBC": {"low": 4.5, "high": 11.0, "unit": "K/uL"},
#     "RBC": {"low": 4.5, "high": 5.9, "unit": "M/uL"},
#     "HGB": {"low": 13.5, "high": 17.5, "unit": "g/dL"},
#     "HCT": {"low": 41.0, "high": 50.0, "unit": "%"},
#     "PLT": {"low": 150, "high": 450, "unit": "K/uL"},
#     "NA": {"low": 135, "high": 145, "unit": "mmol/L"},
#     "K": {"low": 3.5, "high": 5.0, "unit": "mmol/L"},
#     "CREATININE": {"low": 0.7, "high": 1.3, "unit": "mg/dL"},
#     "GLUCOSE": {"low": 70, "high": 100, "unit": "mg/dL"},
#     "TROPONIN": {"low": 0.0, "high": 0.04, "unit": "ng/mL"},
#     "D-DIMER": {"low": 0.0, "high": 500.0, "unit": "ng/mL FEU"},
#     "LACTATE": {"low": 0.5, "high": 1.0, "unit": "mmol/L"},
#     "CRP": {"low": 0.0, "high": 10.0, "unit": "mg/L"},
#     "TSH": {"low": 0.4, "high": 4.0, "unit": "mIU/L"},
#     "A1C": {"low": 4.0, "high": 5.6, "unit": "%"},
# }

# mimic = extract_data.mimic


# lab_mapping = mimic.d_items.set_index("itemid")["label"].to_dict()
# mimic.labevents["LAB_NAME"] = mimic.labevents["itemid"].map(lab_mapping)

# labs_of_interest = list(LAB_REFERENCE_RANGES.keys())
# lab_data = mimic.labevents[mimic.labevents["LAB_NAME"].isin(labs_of_interest)].copy()

# lab_data = lab_data[lab_data["valuenum"].notna()]
# def label_lab(row):
#     lab = row["LAB_NAME"]
#     val = row["valuenum"]
#     low = LAB_REFERENCE_RANGES[lab]["low"]
#     high = LAB_REFERENCE_RANGES[lab]["high"]

#     if val < low:
#         return "LOW"
#     if val > high:
#         return "HIGH"
#     return "NORMAL"

# lab_data["LABEL"] = lab_data.apply(label_lab, axis=1)
# lab_data["UNIT"] = lab_data["LAB_NAME"].map(lambda x: LAB_REFERENCE_RANGES[x]["unit"])
# lab_data["LOW"] = lab_data["LAB_NAME"].map(lambda x: LAB_REFERENCE_RANGES[x]["low"])
# lab_data["HIGH"] = lab_data["LAB_NAME"].map(lambda x: LAB_REFERENCE_RANGES[x]["high"])
# lab_data = lab_data[
#     ["subject_id", "hadm_id", "LAB_NAME", "valuenum",
#      "UNIT", "LOW", "HIGH", "LABEL"]
# ]


def tool_order_labs(
    test_name: str,
    hadm_id: int = None,
    subject_id: int = None,
    tool_context: ToolContext = None
) -> str:
    """
    [TOOL] Returns actual lab results from MIMIC-IV.
    """

    test_key = test_name.upper()
    if test_key not in labs_of_interest:
        return f"{test_key}: Not a supported lab test."

    # Filter relevant rows
    df = lab_data[lab_data["LAB_NAME"] == test_key]

    if hadm_id:
        df = df[df["hadm_id"] == hadm_id]

    if subject_id:
        df = df[df["subject_id"] == subject_id]

    if df.empty:
        return f"No results found for {test_key}."

    row = df.sort_values("valuenum", ascending=False).iloc[0]

    pulled = {
        "test": test_key,
        "value": row["valuenum"],
        "unit": row["UNIT"],
        "flag": row["LABEL"],
        "low": row["LOW"],
        "high": row["HIGH"],
        "subject_id": row["subject_id"],
        "hadm_id": row["hadm_id"],
    }
    if tool_context:
        results = tool_context.state.get("temp:lab_results", [])
        results.append(pulled)
        tool_context.state["temp:lab_results"] = results

    return (
        f"{test_key}: {pulled['value']} {pulled['unit']} "
        f"(Range {pulled['low']}-{pulled['high']}) → {pulled['flag']}"
    )

