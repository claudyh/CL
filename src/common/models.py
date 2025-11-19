from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing import Optional, Literal

class TimeFilter(BaseModel):
  start: Optional[int] = Field(None, description="Start year")
  end: Optional[int] = Field(None, description="End year")

class QueryPlan(BaseModel):
  target: str = Field(..., description="Entity or place being asked about")
  relation: str = Field(..., description="Relation or type of information requested")
  time: TimeFilter = Field(default_factory=TimeFilter, description="Time filter for the query")

  source_type: Optional[Literal["monarchs"]] = Field(
    None,
    description="Best-matching source/table for this question.",
  )

  def as_query(self) -> str:
    base = f"{self.relation} in {self.target}".strip()

    if self.time.start and self.time.end:
      if self.time.start == self.time.end:
        return f"{base} around the year {self.time.start}"
      return f"{base} between the years {self.time.start} and {self.time.end}"

    if self.time.start:
      return f"{base} around the year {self.time.start}"

    return base


class RowData(BaseModel):
  subject: str
  predicate: str
  object: str
  start_date: str
  end_date: str


@dataclass
class CsvSourceConfig:
  name: str               # e.g. "monarchs", "prime_ministers"
  path: str               # e.g. "data/monarchs.csv"
