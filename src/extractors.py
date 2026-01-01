import re
from typing import List, Dict, Any, Optional
from src.schema import BureauParameter, GstSale, ExtractionOutput
from src.loaders import DataLoader
from src.rag import RAGEngine
from src.llm import LLMEngine
from src.utils import extract_number, clean_text

def extract_credit_score_fallback(text: str) -> Optional[int]:
    pattern1 = r'PERFORM\s+CONSUMER\s+[\d.]+\s*(\d{3})-(\d{3})\s*(\d{3})'
    match = re.search(pattern1, text, re.IGNORECASE)
    if match:
        score = int(match.group(3))
        if 300 <= score <= 900:
            return score

    pattern2 = r'(?:CRIF|CIBIL|HM)\s+(?:Score|SCORE).*?(\d{3})\b'
    match = re.search(pattern2, text, re.IGNORECASE)
    if match:
        score = int(match.group(1))
        if 300 <= score <= 900:
            return score
    pattern3 = r'(?:SCORE|Score).*?300[-\s]*900\s*(\d{3})'
    match = re.search(pattern3, text, re.IGNORECASE)
    if match:
        score = int(match.group(1))
        if 300 <= score <= 900:
            return score

    return None

class BureauExtractor:
    def __init__(self, excel_path: str, llm_engine: LLMEngine):
        self.parameters = DataLoader.load_excel_parameters(excel_path)
        self.rag = RAGEngine()
        self.llm = llm_engine

    def extract(self, pdf_path: str) -> Dict[str, BureauParameter]:
        chunks = DataLoader.load_pdf(pdf_path)

        print(f"INFO: Loaded {len(chunks)} chunks from PDF")

        self.rag.index_document(chunks)
        priority_chunks = []

        for chunk in chunks[:10]:  
            if chunk.text and len(chunk.text.strip()) > 50:
                priority_chunks.append(chunk.text)

        queries = [
            "CRIF HM Score PERFORM CONSUMER credit score 300-900 range",
            "CIBIL Score credit rating score",
            "Account Summary Total Current Balance Overdue Amount Active Accounts Number",
            "Payment History DPD Days Past Due STD SMA SUB DBT",
            "Settlement Write-off Suit Filed Wilful Default",
            "Enquiry Summary Credit Inquiries",
            "Sanctioned Amount Disbursed Amount Active Loans",
        ]

        rag_chunks = []
        for query in queries:
            docs = self.rag.retrieve(query, k=3)
            for doc in docs:
                if doc.page_content not in rag_chunks:
                    rag_chunks.append(doc.page_content)

        all_text_parts = priority_chunks + rag_chunks
        filtered_text = "\n---PAGE BREAK---\n".join(all_text_parts[:15])
        if len(filtered_text) > 12000:
            filtered_text = filtered_text[:12000] + "\n...[truncated]"

        print(f"DEBUG: Context length for {pdf_path.split('/')[-1]}: {len(filtered_text)} chars")
        print(f"DEBUG: Context preview (first 500 chars):\n{filtered_text[:500]}")
        if "627" in filtered_text or "SCORE" in filtered_text.upper():
            print("DEBUG: Score information found in context!")
        else:
            print("WARNING: Score may not be in context")
        params_dict = {}
        for param in self.parameters:
            key = param.get('parameter name', param.get('parameter', 'Unknown'))
            desc = param.get('description', key)
            params_dict[key] = desc
            
        results = {}
        try:
            raw_data = self.llm.extract_bulk_parameters(filtered_text, params_dict)
            if raw_data.get("CIBIL Score") is None:
                fallback_score = extract_credit_score_fallback(filtered_text)
                if fallback_score:
                    raw_data["CIBIL Score"] = fallback_score
                    print(f"DEBUG: Fallback extraction found credit score: {fallback_score}")
            for key in params_dict.keys():
                val = raw_data.get(key)
                final_value = val
                confidence = 0.0
                source = "Not Found"
                if isinstance(val, str):
                    if val.lower() in ['null', 'not found', 'n/a', 'na']:
                        final_value = None
                        confidence = 0.0
                        source = "Not Found"
                    else:
                        num = extract_number(val)
                        if num is not None and len(val) < 20:
                            final_value = num
                            confidence = 0.85  
                            source = "Bureau Report - RAG Analysis"
                        else:
                            final_value = val
                            confidence = 0.75  
                            source = "Bureau Report - RAG Analysis"
                elif isinstance(val, (int, float)):
                    final_value = val
                    confidence = 0.90  
                    source = "Bureau Report - RAG Analysis"
                elif val is None:
                    final_value = None
                    confidence = 0.0
                    source = "Not Found"
                else:
                    final_value = val
                    confidence = 0.70
                    source = "Bureau Report - RAG Analysis"

                results[key] = BureauParameter(
                    value=final_value,
                    source=source,
                    confidence=confidence
                )

        except Exception as e:
            print(f"Bulk extraction failed: {e}")
            for key in params_dict.keys():
                 results[key] = BureauParameter(
                    value=None,
                    source="Extraction Error",
                    confidence=0.0
                )
        self.rag.clear()
            
        return results

class GstExtractor:
    def __init__(self, llm_engine: LLMEngine):
        self.llm = llm_engine

    def extract(self, pdf_path: str) -> List[GstSale]:
        chunks = DataLoader.load_pdf(pdf_path)
        sales_data = []
        
        for chunk in chunks:
            if "3.1" in chunk.text and "Outward taxable supplies" in chunk.text:
                prompt = f"""
                Context:
                {chunk.text}
                
                Task: Extract the 'Period' (Month and Year) and the 'Total Taxable Value' from Table 3.1 row (a) 'Outward taxable supplies'.
                
                Return format: JSON
                {{
                    "month": "Month Year",
                    "sales": 12345.00
                }}
                If not found, return empty JSON {{}}.
                """
                try:
                    if self.llm.model:
                        response = self.llm.model.invoke(prompt)
                        txt = response.strip()
                        txt = txt.replace('```json', '').replace('```', '')
                        import json
                        try:
                            data = json.loads(txt)
                            if data and 'sales' in data:
                                sales_data.append(GstSale(
                                    month=data.get('month', 'Unknown'),
                                    sales=float(str(data.get('sales')).replace(',', '')),
                                    source=f"GSTR-3B Table 3.1(a) (Page {chunk.page_number})",
                                    confidence=0.95
                                ))
                        except:
                            pass 
                except Exception as e:
                    print(f"GST Extraction error: {e}")
                    
        return sales_data
