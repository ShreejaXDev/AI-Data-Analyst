from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    dataset_id: str
    filename: str
    rows: int
    columns: int
    column_names: List[str]
    missing_values: Dict[str, int]
    duplicate_rows: int
    dtypes: Dict[str, str]
    preview: List[Dict[str, Any]]


class ChatRequest(BaseModel):
    dataset_id: str = Field(..., description="Active dataset/session identifier")
    message: str = Field(..., description="User natural language question or instruction")


class ActionDetail(BaseModel):
    iteration: Optional[int] = None
    action: str
    description: Optional[str] = ""
    code: Optional[str] = None
    result: Optional[Any] = None


class ChatResponse(BaseModel):
    answer: str
    dataset_id: str
    chart: Optional[str] = None
    actions: List[Dict[str, Any]] = []
    success: bool = True


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "AI Data Analyst"


class ErrorResponse(BaseModel):
    detail: str
