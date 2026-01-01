from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class BureauParameter(BaseModel):
    value: Optional[Any] = None
    source: str = "Unknown"
    confidence: float = 0.0

class GstSale(BaseModel):
    month: str
    sales: float
    source: str = "GSTR-3B Table 3.1(a)"
    confidence: float = 1.0

class ExtractionOutput(BaseModel):
    bureau_parameters: Dict[str, BureauParameter] = Field(default_factory=dict)
    gst_sales: List[GstSale] = Field(default_factory=list)
    overall_confidence_score: float = 0.0

    def to_json(self):
        return self.model_dump(mode='json')
