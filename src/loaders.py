import pandas as pd
from pypdf import PdfReader
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class DocumentChunk:
    text: str
    page_number: int
    source_file: str

class DataLoader:
    @staticmethod
    def load_pdf(file_path: str) -> List[DocumentChunk]:
        reader = PdfReader(file_path)
        chunks = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                chunks.append(DocumentChunk(
                    text=text,
                    page_number=i + 1,
                    source_file=file_path.split('/')[-1]
                ))
        return chunks

    @staticmethod
    def load_excel_parameters(file_path: str) -> List[Dict]:
        try:
            df = pd.read_excel(file_path)
            df.columns = [c.lower().strip() for c in df.columns]
            return df.to_dict(orient='records')
        except Exception as e:
            print(f"Error loading Excel: {e}")
            return []
