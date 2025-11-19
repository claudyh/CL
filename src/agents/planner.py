from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from src.common.models import QueryPlan


PLANNER_SYSTEM_PROMPT = SystemMessage(
  "You convert questions about historical and political facts involving Portugal "
  "into a JSON object matching the provided schema. Return ONLY valid JSON.\n\n"
  "Schema fields:\n"
  "- 'target': always 'Portugal' (string), unless user explicitly asks otherwise.\n"
  "- 'relation': short phrase describing the relation, using the user's wording "
  "  (e.g. 'ruled', 'head of state', 'king', 'prime minister', 'war', 'treaty').\n"
  "- 'time.start': year mentioned in the question (integer) or null.\n"
  "- 'time.end': year mentioned in the question (integer) or null.\n"
  "- 'source_type': which data source is most relevant to answer the question. "
  "  One of: 'monarchs', 'prime_ministers', 'wars', 'treaties', 'economy'. "
  "  For kings/monarchs/head of state -> 'monarchs'. "
  "  For prime ministers -> 'prime_ministers'. "
  "  For wars/conflicts -> 'wars'. "
  "  For international agreements -> 'treaties'. "
  "  For economic indicators -> 'economy'.\n\n"
  "Rules:\n"
  "1. If the place is not explicitly specified but clearly implied, use 'Portugal' as target.\n"
  "2. Do NOT normalize 'relation'; keep the user's wording.\n"
  "3. If a specific year is mentioned, set both 'time.start' and 'time.end' to that year.\n"
  "4. If a range is mentioned (e.g. 'around 1830-1840'), set 'time.start' and 'time.end' accordingly.\n"
  "5. Always pick the single best 'source_type' from the list, never something else.\n"
)

planner_llm = ChatOllama(
  model="llama3.1:8b",
  temperature=0
)

llm_structured = planner_llm.with_structured_output(schema=QueryPlan)

def parse_plan(question: str) -> QueryPlan:
  return llm_structured.invoke([
    PLANNER_SYSTEM_PROMPT,
    HumanMessage(question)
  ])