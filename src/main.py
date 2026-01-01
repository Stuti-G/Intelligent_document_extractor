import argparse
import json
import os
import sys
from pathlib import Path

import sys
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import EXCEL_PARAM_FILE, BUREAU_REPORTS_DIR, GST_RETURNS_DIR
from src.llm import LLMEngine
from src.extractors import BureauExtractor, GstExtractor
from src.schema import ExtractionOutput

def serialize(obj):
    if hasattr(obj, 'to_json'):
        return obj.to_json()
    if hasattr(obj, 'model_dump'):
        return obj.model_dump(mode='json')
    return obj.__dict__

def main():
    parser = argparse.ArgumentParser(description="Document Extraction Tool")
    parser.add_argument("--file", type=str, help="Path to PDF file")
    parser.add_argument("--type", type=str, choices=["bureau", "gst", "auto"], default="auto", help="Document type")
    parser.add_argument("--process-all", action="store_true", help="Process all files in data directories")
    args = parser.parse_args()

    llm = LLMEngine() 
    bureau_extractor = BureauExtractor(str(EXCEL_PARAM_FILE), llm)
    gst_extractor = GstExtractor(llm)

    results = []

    files_to_process = []
    
    if args.process_all:
        if BUREAU_REPORTS_DIR.exists():
            for f in BUREAU_REPORTS_DIR.glob("*.pdf"):
                files_to_process.append((f, "bureau"))
        
        if GST_RETURNS_DIR.exists():
            for f in GST_RETURNS_DIR.glob("*.pdf"):
                files_to_process.append((f, "gst"))
    elif args.file:
        f = Path(args.file)
        if not f.exists():
            print(f"File not found: {f}")
            return
        dtype = args.type
        if dtype == "auto":
            if "bureau" in str(f).lower() or "crif" in str(f).lower() or "report" in str(f).lower():
                dtype = "bureau"
            elif "gst" in str(f).lower() or "3b" in str(f).lower():
                dtype = "gst"
            else:
                print("Could not auto-detect type. Please specify --type")
                return
        files_to_process.append((f, dtype))
    else:
        parser.print_help()
        return

    final_output = {}

    for file_path, dtype in files_to_process:
        print(f"Processing {file_path} as {dtype}...")
        try:
            if dtype == "bureau":
                data = bureau_extractor.extract(str(file_path))
                final_output[file_path.name] = {"bureau_parameters": {k: v.model_dump() for k,v in data.items()}}
            elif dtype == "gst":
                data = gst_extractor.extract(str(file_path))
                final_output[file_path.name] = {"gst_sales": [d.model_dump() for d in data]}
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            final_output[file_path.name] = {"error": str(e)}
        
        import time
        print("Waiting 5s before next file...")
        time.sleep(5)

        with open("extraction_results.json", "w") as f:
            json.dump(final_output, f, indent=2, default=serialize)
        print(f"Intermediate results saved for {file_path.name}")

    print(json.dumps(final_output, indent=2, default=serialize))
    with open("extraction_results.json", "w") as f:
        json.dump(final_output, f, indent=2, default=serialize)
    print("\nResults saved to extraction_results.json")

if __name__ == "__main__":
    main()
