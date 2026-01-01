from typing import Optional, Dict, Any
import json
import re
from langchain_community.llms import Ollama
from src.config import LLM_MODEL_NAME

class LLMEngine:
    def __init__(self):
        self.model = Ollama(model=LLM_MODEL_NAME, temperature=0.1)
        print(f"Initialized LLM Engine with Ollama model: {LLM_MODEL_NAME}")

    def extract_value(self, context: str, parameter_name: str, parameter_description: str) -> str:
        prompt = f"""
        You are a precise data extraction assistant.
        Context:
        {context}

        Task: Extract the value for the parameter "{parameter_name}".
        Description: {parameter_description}
        
        Rules:
        1. Return ONLY the value. No explanation, no markdown.
        2. If the value is a number, format it as a plain number (no commas, no currency symbols).
        3. If not found in the context, return "null".
        4. If multiple values exist, pick the most relevant one based on the description.
        """
        
        try:
            response = self.model.invoke(prompt)
            return response.strip()
        except Exception as e:
            print(f"LLM Error: {e}")
            return "error"

    def extract_bulk_parameters(self, context: str, parameters: dict) -> dict:
        """
        Extracts multiple parameters at once.
        parameters: dict of {name: description}
        Returns: dict of {name: value}
        """
        import json

        params_list = []
        for name, desc in parameters.items():
            params_list.append(f'- "{name}": {desc}')

        params_text = '\n'.join(params_list)

        prompt = f"""You are a credit bureau data extraction expert. Extract the following credit parameters from the bureau report text below.

PARAMETERS TO EXTRACT:
{params_text}

BUREAU REPORT TEXT:
{context}

EXTRACTION RULES:
1. Look for exact values in the text
2. For "CIBIL Score": This may appear as "CIBIL Score", "CRIF Score", "CRIF HM Score", or "PERFORM CONSUMER" followed by a score number (typically 300-900 range). Look for patterns like "PERFORM CONSUMER 2.2300-900627" where 627 is the score.
3. For DPD (Days Past Due): Count total occurrences of delinquency in payment history (look for SMA, SUB, DBT, LSS, or any non-STD status codes)
4. For "Credit Inquiries": Look in "Enquiry Summary" section or count recent credit inquiries
5. For "Max Active Loans": Look in "Account Summary" for "Active Accounts" or "Number of Accounts"
6. For "Total Amount Overdue": Look in "Account Summary" for "Total Amount Overdue" or "Overdue Amt"
7. For loan counts: Count number of active accounts or loans from account summary
8. For amounts: Extract numeric values, remove commas and currency symbols
9. For yes/no questions: Return true/false based on presence of indicators
10. If you cannot find a value, return null
11. Return ONLY valid JSON, no explanations

EXTRACTION EXAMPLES:
- If you see "PERFORM CONSUMER 2.2300-900627", extract 627 as the CIBIL Score
- If you see "Active Accounts: 25", extract 25 as Max Active Loans
- If you see "000/STD" in payment history, that means 0 DPD (no delinquency)
- If you see "030/SMA" or "060/SUB", count those as delinquency days

OUTPUT FORMAT (JSON only):
{{
  "CIBIL Score": <number or null>,
  "NTC Accepted": <true/false/null>,
  "Overdue Threshold": <number or null>,
  "30+ DPD (Configurable Period)": <number or null>,
  "60+ DPD (Configurable Period)": <number or null>,
  "90+ DPD (Configurable Period)": <number or null>,
  "Settlement / Write-off": <true/false/null>,
  "No Live PL/BL": <true/false/null>,
  "Suit Filed": <true/false/null>,
  "Wilful Default": <true/false/null>,
  "Written-off Debt Amount": <number or null>,
  "Max Loans": <number or null>,
  "Loan Amount Threshold": <number or null>,
  "Credit Inquiries": <number or null>,
  "Max Active Loans": <number or null>
}}

RESPOND WITH JSON ONLY:"""

        try:
            response = self.model.invoke(prompt)

            text = response.strip()
            print(f"DEBUG: Raw LLM response length: {len(text)} chars")
            print(f"DEBUG: First 200 chars: {text[:200]}")

            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "")
            elif text.startswith("```"):
                text = text.replace("```", "")

            text = text.strip()

            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                text = text[start:end]
            else:
                print(f"ERROR: Could not find JSON in response")
                return {}

            result = json.loads(text)
            print(f"DEBUG: Successfully parsed JSON with {len(result)} keys")

            if "CIBIL Score" in result:
                print(f"DEBUG: Extracted CIBIL Score: {result['CIBIL Score']}")

            return result
        except json.JSONDecodeError as e:
            print(f"LLM JSON Parse Error: {e}")
            print(f"Text that failed to parse: {text if 'text' in locals() else 'None'}")
            return {}
        except Exception as e:
            print(f"LLM Bulk Error: {e}")
            print(f"Raw Response: {text if 'text' in locals() else 'None'}")
            return {}
