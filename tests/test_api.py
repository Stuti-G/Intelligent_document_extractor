import requests
import json
from pathlib import Path
import sys

API_BASE_URL = "http://localhost:8000"


def test_health():
    print("\n" + "="*60)
    print("Testing Health Endpoint")
    print("="*60)

    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_bureau_extraction(pdf_path: str):
    print("\n" + "="*60)
    print(f"Testing Bureau Extraction: {Path(pdf_path).name}")
    print("="*60)

    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
            response = requests.post(
                f"{API_BASE_URL}/api/extract/bureau",
                files=files
            )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\nExtracted Parameters:")
            print(f"Overall Confidence: {result.get('overall_confidence_score', 0)}")

            if result.get('bureau_parameters'):
                print(f"\nSample Parameters (first 5):")
                params = result['bureau_parameters']
                for i, (key, value) in enumerate(list(params.items())[:5]):
                    print(f"  {key}: {value.get('value')} (confidence: {value.get('confidence')})")

            return True
        else:
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False


def test_gst_extraction(pdf_path: str):
    print("\n" + "="*60)
    print(f"Testing GST Extraction: {Path(pdf_path).name}")
    print("="*60)

    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
            response = requests.post(
                f"{API_BASE_URL}/api/extract/gst",
                files=files
            )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\nExtracted GST Sales:")
            print(f"Overall Confidence: {result.get('overall_confidence_score', 0)}")

            if result.get('gst_sales'):
                print(f"\nMonthly Sales:")
                for sale in result['gst_sales']:
                    print(f"  {sale['month']}: {sale['sales']} (confidence: {sale.get('confidence')})")

            return True
        else:
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False


def test_auto_extraction(pdf_path: str):
    print("\n" + "="*60)
    print(f"Testing Auto Extraction: {Path(pdf_path).name}")
    print("="*60)

    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (Path(pdf_path).name, f, 'application/pdf')}
            response = requests.post(
                f"{API_BASE_URL}/api/extract/auto",
                files=files
            )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)[:500]}...")

        return response.status_code == 200

    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    print("\n" + "="*60)
    print("API TEST SUITE")
    print("="*60)

    print("\nChecking if API server is running...")
    try:
        requests.get(API_BASE_URL)
        print("✓ Server is running")
    except:
        print("✗ Server is not running!")
        print(f"\nPlease start the server first:")
        print(f"  python api/main.py")
        print(f"  or")
        print(f"  uvicorn api.main:app --reload")
        sys.exit(1)

    test_health()

    base_dir = Path(__file__).parent.parent
    bureau_files = list((base_dir / "data" / "Bureau_Reports").glob("*.pdf"))
    gst_files = list((base_dir / "data" / "GST_3B_Returns").glob("*.pdf"))

    if bureau_files:
        test_bureau_extraction(str(bureau_files[0]))
    else:
        print("\nNo bureau files found to test")

    if gst_files:
        test_gst_extraction(str(gst_files[0]))
    else:
        print("\nNo GST files found to test")

    if bureau_files:
        test_auto_extraction(str(bureau_files[0]))

    print("\n" + "="*60)
    print("API Tests Complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
