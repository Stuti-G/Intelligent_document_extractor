# Document Intelligence: Bureau & GST Data Extraction

AI-powered document extraction system for CRIF Bureau Reports and GSTR-3B Returns using LLMs, RAG, and embeddings.

## Architecture

```
PDF Document → PDF Loader → RAG Engine (ChromaDB + Embeddings) → LLM (Mistral via Ollama) → JSON Output
```

## Prerequisites

- Python 3.13+
- Ollama with Mistral model
- 
## Quick Start

### 1. Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull mistral
```
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

## Technical Details

### RAG Implementation

1. **Document Chunking**: PDFs split into page-level chunks
2. **Embedding**: Each chunk embedded using `all-MiniLM-L6-v2`
3. **Similarity Search**: Retrieve top-k relevant chunks using cosine similarity
4. **LLM Extraction**: Mistral extracts values from retrieved context
5. **Fallback Extraction**: Regex-based fallback for critical fields (e.g., credit score)

## Testing

**Run Extraction Tests:**
```bash
python tests/test_extraction.py
```

**Run API Tests (server must be running):**
```bash
python tests/test_api.py
```
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
