from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
from uuid import uuid4

class SubmissionStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class RunRequest(BaseModel):
    """Payload when a user runs code with their own sample test cases."""
    source_code: str
    language_id: str
    test_cases: List[str] # Or more complex test case structure
    expected_outputs: Optional[List[str]] = None

class SubmitRequest(BaseModel):
    """Payload when a user submits code against a specific problem."""
    source_code: str
    language_id: str
    problem_id: str

class Submission(BaseModel):
    """MongoDB Document Model for a Submission."""
    id: str = Field(default_factory=lambda: str(uuid4()), alias="_id")
    type: str  # "run" or "submit"
    source_code: str
    language_id: str
    problem_id: Optional[str] = None
    status: SubmissionStatus = SubmissionStatus.PENDING
    test_cases: Optional[List[str]] = None
    expected_outputs: Optional[List[str]] = None
    results: Optional[List[Dict[str, Any]]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
