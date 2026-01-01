# Document Intelligence: Bureau & GST Data Extraction

AI-powered document extraction system for CRIF Bureau Reports and GSTR-3B Returns using LLMs, RAG, and embeddings.

## Features

- **Bureau Report Extraction**: Extract credit parameters from CRIF bureau PDFs (CIBIL Score, DPD, Active Loans, etc.)
- **GST Return Extraction**: Extract monthly sales timeline from GSTR-3B PDFs
- **RAG-based Retrieval**: Uses embeddings (MiniLM-L6-v2) and ChromaDB for accurate context retrieval
- **Confidence Scoring**: Each extracted value includes confidence score and source attribution
- **FastAPI Backend**: Production-ready REST API with Swagger documentation

## Architecture

```
PDF Document → PDF Loader → RAG Engine (ChromaDB + Embeddings) → LLM (Mistral via Ollama) → JSON Output
```

## Prerequisites

- Python 3.13+
- Ollama with Mistral model
- 8GB RAM minimum

## Quick Start

### 1. Install Ollama

**macOS:**
```bash
brew install ollama
brew services start ollama
ollama pull mistral
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull mistral
```

**Windows:** Download from [https://ollama.com](https://ollama.com)

### 2. Install Dependencies

```bash
source .venv/bin/activate  # Activate virtual environment
pip install -r requirements.txt
```

### 3. Start the API Server

```bash
python api/main.py
```

API will be available at `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

## Usage

### Option 1: API Endpoints

**Extract Bureau Report:**
```bash
curl -X POST http://localhost:8000/api/extract/bureau \
  -F "file=@data/Bureau_Reports/JEET  ARORA_PARK251217CR671901414.pdf"
```

**Extract GST Return:**
```bash
curl -X POST http://localhost:8000/api/extract/gst \
  -F "file=@data/GST_3B_Returns/GSTR3B_06AAICK4577H1Z8_042025.pdf"
```

**Auto-detect Document Type:**
```bash
curl -X POST http://localhost:8000/api/extract/auto \
  -F "file=@data/Bureau_Reports/sample.pdf"
```

### Option 2: Command Line

**Process Single File:**
```bash
python src/main.py --file "data/Bureau_Reports/JEET  ARORA_PARK251217CR671901414.pdf" --type bureau
```

**Process All Files:**
```bash
python src/main.py --process-all
```

Results are saved to `extraction_results.json`.

## Output Schema

### Bureau Extraction

```json
{
  "bureau_parameters": {
    "CIBIL Score": {
      "value": 627,
      "source": "Bureau Report - RAG Analysis",
      "confidence": 0.9
    },
    "NTC Accepted": {
      "value": true,
      "source": "Bureau Report - RAG Analysis",
      "confidence": 0.9
    },
    "30+ DPD (Configurable Period)": {
      "value": 0,
      "source": "Bureau Report - RAG Analysis",
      "confidence": 0.9
    }
  },
  "overall_confidence_score": 0.82
}
```

### GST Extraction

```json
{
  "gst_sales": [
    {
      "month": "April 2025",
      "sales": 976171,
      "source": "GSTR-3B Table 3.1(a)",
      "confidence": 0.95
    }
  ],
  "overall_confidence_score": 0.95
}
```

## Project Structure

```
Assignment_2/
├── api/
│   ├── __init__.py
│   └── main.py                 # FastAPI application
├── src/
│   ├── config.py               # Configuration settings
│   ├── llm.py                  # LLM engine (Ollama/Mistral)
│   ├── loaders.py              # PDF/Excel loaders
│   ├── rag.py                  # RAG engine with ChromaDB
│   ├── extractors.py           # Bureau & GST extractors
│   ├── schema.py               # Pydantic models
│   ├── utils.py                # Helper functions
│   └── main.py                 # CLI script
├── tests/
│   ├── __init__.py
│   ├── test_extraction.py      # Extraction tests
│   └── test_api.py             # API tests
├── data/
│   ├── Bureau_Reports/         # Sample bureau PDFs (6 files)
│   ├── GST_3B_Returns/         # Sample GST PDFs (6 files)
│   └── Bureau parameters - Report.xlsx
├── requirements.txt
└── README.md
```

## Extraction Parameters

**Bureau Report Parameters:**
- CIBIL Score (300-900 range)
- NTC Accepted (true/false)
- Overdue Threshold
- 30+/60+/90+ DPD (Days Past Due)
- Settlement / Write-off
- No Live PL/BL
- Suit Filed
- Wilful Default
- Written-off Debt Amount
- Max Loans
- Loan Amount Threshold
- Credit Inquiries
- Max Active Loans

**GST-3B Parameters:**
- Month (filing period)
- Sales (Total taxable outward supplies from Table 3.1(a))

## Technical Details

### RAG Implementation

1. **Document Chunking**: PDFs split into page-level chunks
2. **Embedding**: Each chunk embedded using `all-MiniLM-L6-v2`
3. **Similarity Search**: Retrieve top-k relevant chunks using cosine similarity
4. **LLM Extraction**: Mistral extracts values from retrieved context
5. **Fallback Extraction**: Regex-based fallback for critical fields (e.g., credit score)

### Confidence Score Calculation

- **0.95**: High confidence (GST sales from structured tables)
- **0.90**: Direct numeric values from LLM
- **0.85**: Numeric values parsed from strings
- **0.75**: String values extracted
- **0.70**: Other types (boolean, etc.)
- **0.00**: Value not found

## Configuration

Edit `src/config.py` to customize:

```python
# Models
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
LLM_MODEL_NAME = "mistral"
LLM_PROVIDER = "ollama"

# Paths
EXCEL_PARAM_FILE = DATA_DIR / "Bureau parameters - Report.xlsx"
```

## Testing

**Run Extraction Tests:**
```bash
python tests/test_extraction.py
```

**Run API Tests (server must be running):**
```bash
python tests/test_api.py
```

## Performance

Approximate processing times (M1 Mac):
- Bureau Report (60 pages): ~30-45 seconds
- GST Return (6 pages): ~10-15 seconds

## Troubleshooting

### Ollama Connection Error
```bash
ollama serve  # Start Ollama server
```

### Model Not Found
```bash
ollama pull mistral
```

### Low Extraction Accuracy
- Increase RAG retrieval count in `src/extractors.py`
- Try larger LLM model: `ollama pull llama3`
- Improve parameter descriptions in Excel file

## Tech Stack

- **Backend**: FastAPI, Uvicorn
- **LLM**: Ollama (Mistral 7B)
- **Embeddings**: sentence-transformers (MiniLM-L6-v2)
- **Vector DB**: ChromaDB
- **PDF Parsing**: PyPDF
- **Data Validation**: Pydantic
- **RAG Framework**: LangChain

## License

MIT
