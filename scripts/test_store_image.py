import importlib.util
import pathlib
import sys
import base64


mod_path = pathlib.Path(__file__).resolve().parents[1] / "medagent" / "patient_db_tool.py"
spec = importlib.util.spec_from_file_location("patient_db_tool", str(mod_path))
patient_db_tool = importlib.util.module_from_spec(spec)
sys.modules["patient_db_tool"] = patient_db_tool
spec.loader.exec_module(patient_db_tool)

store_patient_file_in_db = patient_db_tool.store_patient_file_in_db
get_patient_file_from_db = patient_db_tool.get_patient_file_from_db

PATIENT_ID = "TEST-IMG-001"
ITEM_TYPE = "2D image"
png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="
FILENAME = "tiny.png"
MIME = "image/png"

if __name__ == "__main__":

    store_patient_file_in_db(PATIENT_ID, ITEM_TYPE, png_b64, filename=FILENAME, mime_type=MIME)
    files = get_patient_file_from_db(PATIENT_ID, ITEM_TYPE)
    if not files:
        print("No files retrieved")
    else:
        print(f"Found {len(files)} file(s)")
        for i, fi in enumerate(files):
            print(f"File[{i}] metadata: filename={fi.get('filename')}, mime_type={fi.get('mime_type')}, created_at={fi.get('created_at')}, size={(len(fi.get('data')) if fi.get('data') else 0)}")
        data = files[-1]["data"]
        with open("out_test_image.png", "wb") as f:
            f.write(data)
        print(f"Wrote last file ({len(data)} bytes) to out_test_image.png")
