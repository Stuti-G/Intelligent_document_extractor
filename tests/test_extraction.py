import sys
import os
from pathlib import Path
import json
from typing import Dict, List, Any
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import EXCEL_PARAM_FILE, BUREAU_REPORTS_DIR, GST_RETURNS_DIR
from src.llm import LLMEngine
from src.extractors import BureauExtractor, GstExtractor


class ExtractionTester:
    def __init__(self):
        self.llm = LLMEngine()
        self.bureau_extractor = BureauExtractor(str(EXCEL_PARAM_FILE), self.llm)
        self.gst_extractor = GstExtractor(self.llm)

    def test_bureau_consistency(self, pdf_path: str, num_runs: int = 5) -> Dict[str, Any]:
        print(f"\n{'='*60}")
        print(f"Testing Bureau Report Consistency: {Path(pdf_path).name}")
        print(f"Number of runs: {num_runs}")
        print(f"{'='*60}\n")

        results = []

        for i in range(num_runs):
            print(f"Run {i+1}/{num_runs}...", end=" ")
            try:
                extracted = self.bureau_extractor.extract(pdf_path)
                results.append({
                    k: v.model_dump() for k, v in extracted.items()
                })
                print("✓")
            except Exception as e:
                print(f"✗ Error: {e}")

        if not results:
            return {"error": "No successful runs"}

        consistency_report = {}
        for param_name in results[0].keys():
            values = [r[param_name]['value'] for r in results]
            unique_values = set(str(v) for v in values)

            consistency_report[param_name] = {
                "unique_values": len(unique_values),
                "values": list(unique_values),
                "consistency_score": 1.0 if len(unique_values) == 1 else 0.0,
                "most_common": max(set(values), key=values.count) if values else None
            }

        consistency_scores = [v['consistency_score'] for v in consistency_report.values()]
        overall_consistency = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.0

        return {
            "num_runs": num_runs,
            "successful_runs": len(results),
            "overall_consistency": round(overall_consistency, 2),
            "parameter_consistency": consistency_report,
            "sample_result": results[0]
        }

    def test_gst_consistency(self, pdf_path: str, num_runs: int = 5) -> Dict[str, Any]:
        print(f"\n{'='*60}")
        print(f"Testing GST Return Consistency: {Path(pdf_path).name}")
        print(f"Number of runs: {num_runs}")
        print(f"{'='*60}\n")

        results = []

        for i in range(num_runs):
            print(f"Run {i+1}/{num_runs}...", end=" ")
            try:
                extracted = self.gst_extractor.extract(pdf_path)
                results.append([item.model_dump() for item in extracted])
                print("✓")
            except Exception as e:
                print(f"✗ Error: {e}")

        if not results:
            return {"error": "No successful runs"}

        lengths = [len(r) for r in results]
        length_consistency = 1.0 if len(set(lengths)) == 1 else 0.0

        if length_consistency == 1.0 and len(results[0]) > 0:
            sales_consistency = []
            for idx in range(len(results[0])):
                sales_values = [r[idx]['sales'] for r in results]
                unique_sales = set(sales_values)
                sales_consistency.append(1.0 if len(unique_sales) == 1 else 0.0)

            overall_consistency = sum(sales_consistency) / len(sales_consistency)
        else:
            overall_consistency = 0.0

        return {
            "num_runs": num_runs,
            "successful_runs": len(results),
            "overall_consistency": round(overall_consistency, 2),
            "length_consistency": length_consistency,
            "sample_result": results[0] if results else []
        }

    def test_accuracy_against_expected(
        self,
        pdf_path: str,
        expected_values: Dict[str, Any],
        doc_type: str = "bureau"
    ) -> Dict[str, Any]:
        print(f"\n{'='*60}")
        print(f"Testing Accuracy: {Path(pdf_path).name}")
        print(f"{'='*60}\n")

        if doc_type == "bureau":
            extracted = self.bureau_extractor.extract(pdf_path)
            extracted_dict = {k: v.value for k, v in extracted.items()}
        else:
            extracted = self.gst_extractor.extract(pdf_path)
            extracted_dict = {f"month_{i}": item.sales for i, item in enumerate(extracted)}

        accuracy_report = {}
        for param, expected_val in expected_values.items():
            extracted_val = extracted_dict.get(param)

            match = extracted_val == expected_val
            accuracy_report[param] = {
                "expected": expected_val,
                "extracted": extracted_val,
                "match": match,
                "accuracy": 1.0 if match else 0.0
            }

        accuracy_scores = [v['accuracy'] for v in accuracy_report.values()]
        overall_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0

        return {
            "overall_accuracy": round(overall_accuracy, 2),
            "total_parameters": len(expected_values),
            "correct_parameters": sum(1 for v in accuracy_report.values() if v['match']),
            "parameter_accuracy": accuracy_report
        }


def run_basic_tests():
    tester = ExtractionTester()

    bureau_files = list(BUREAU_REPORTS_DIR.glob("*.pdf"))
    gst_files = list(GST_RETURNS_DIR.glob("*.pdf"))

    print("\n" + "="*60)
    print("DOCUMENT EXTRACTION - TEST SUITE")
    print("="*60)

    results = {
        "bureau_tests": [],
        "gst_tests": []
    }

    if bureau_files:
        print(f"\nFound {len(bureau_files)} Bureau Report(s)")
        test_file = bureau_files[0]
        consistency = tester.test_bureau_consistency(str(test_file), num_runs=3)
        results["bureau_tests"].append({
            "file": test_file.name,
            "test_type": "consistency",
            "result": consistency
        })

    if gst_files:
        print(f"\nFound {len(gst_files)} GST Return(s)")
        test_file = gst_files[0]
        consistency = tester.test_gst_consistency(str(test_file), num_runs=3)
        results["gst_tests"].append({
            "file": test_file.name,
            "test_type": "consistency",
            "result": consistency
        })

    output_file = Path(__file__).parent / "test_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Test results saved to: {output_file}")
    print(f"{'='*60}\n")

    print("\nTEST SUMMARY:")
    print("-" * 60)

    if results["bureau_tests"]:
        for test in results["bureau_tests"]:
            if "overall_consistency" in test["result"]:
                print(f"Bureau Report: {test['file']}")
                print(f"  Consistency Score: {test['result']['overall_consistency']}")

    if results["gst_tests"]:
        for test in results["gst_tests"]:
            if "overall_consistency" in test["result"]:
                print(f"GST Return: {test['file']}")
                print(f"  Consistency Score: {test['result']['overall_consistency']}")

    print()


if __name__ == "__main__":
    run_basic_tests()
