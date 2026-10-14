from pydantic import BaseModel
from typing import Optional


class IncidentReport(BaseModel):
    description: str
    location: str
    reporter_name: Optional[str] = "Anonymous"