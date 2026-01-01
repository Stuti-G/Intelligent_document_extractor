import re

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_number(text: str) -> float | None:
    if not text:
        return None
    match = re.search(r'[\d,]+\.?\d*', text)
    if match:
        num_str = match.group(0).replace(',', '')
        try:
            return float(num_str)
        except ValueError:
            return None
    return None
