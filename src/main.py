from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import json, re
from typing import Dict, Any, Optional, List
from retrieve import retrieve
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState

from dotenv import load_dotenv
load_dotenv()


llm = ChatOllama(
  model="llama3.1:8b",
  validate_model_on_init=True,
  temperature=0,
)

class TimeFilter(BaseModel):
  start: Optional[int] = Field(None, description="Start year")
  end: Optional[int] = Field(None, description="End year")

class QueryPlan(BaseModel):
  target: str = Field(..., description="Entity or place being asked about")
  relation: str = Field(..., description="Relation or type of information requested")
  time: TimeFilter = Field(default_factory=TimeFilter, description="Time filter for the query")

state: MessagesState = [
  SystemMessage(
    "You convert questions about historical rulers of Portugal into a JSON object "
    "matching the provided schema. Return ONLY valid JSON.\n"
    "Rules:\n"
    "1. 'target' is always 'Portugal'.\n"
    "2. 'relation' should be 'head of state' or similar.\n"
    "3. Set 'start'/'end' if the question specifies a time period.\n"
    "4. If a specific year is mentioned, set both to that year.\n"
    "5. If a range is mentioned (e.g., 'around 1830-1840'), set both accordingly."
  )
]

llm_structured = llm.with_structured_output(schema=QueryPlan)

def parse_plan(question: str) -> QueryPlan:
  msg = state + [HumanMessage(content=question)]
  return llm_structured.invoke(msg)


def main():
  for q in [
    "Who ruled Portugal in the year of 1500?",
    "Who ruled Portugal in 1211?",
    "List rulers of Portugal around 1830-1840.",
    "Who was the head of state of Portugal?"
  ]:
    print(f"\nQ: {q}")
    print(parse_plan(q))

if __name__ == "__main__":
  main()