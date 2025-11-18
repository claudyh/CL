from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict

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


@dataclass
class CsvSourceConfig:
  name: str               # e.g. "monarchs", "prime_ministers"
  path: str               # e.g. "data/monarchs.csv"
  subject_col: str        # name column
  predicate_col: Optional[str] = None
  object_col: Optional[str] = None
  start_date_col: Optional[str] = None
  end_date_col: Optional[str] = None
  extra_metadata: Dict[str, str] = None  # static metadata for all rows of this source