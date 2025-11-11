from pydantic import BaseModel, Field
from typing import Optional

class TimeFilter(BaseModel):
  start: Optional[int] = Field(None, description="Start year")
  end: Optional[int] = Field(None, description="End year")

class QueryPlan(BaseModel):
  target: str = Field(..., description="Entity or place being asked about")
  relation: str = Field(..., description="Relation or type of information requested")
  time: TimeFilter = Field(default_factory=TimeFilter, description="Time filter for the query")