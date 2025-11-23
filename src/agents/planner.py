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
  "  One of: 'monarchs', 'battles'.\n\n"
  "Classification rules for 'source_type':\n"
  "- Use 'monarchs' when the question is mainly about:\n"
  "    * kings, queens, monarchs, dynasties, royal families\n"
  "    * who ruled, who was head of state, sovereign, crown\n"
  "    * succession, reign periods, who was on the throne\n"
  "  Examples (monarchs):\n"
  "    - 'Who was the king of Portugal in 1800?'\n"
  "    - 'Quem reinava em Portugal durante as invasões francesas?'\n"
  "    - 'Who was the head of state of Portugal in 1910?'\n"
  "\n"
  "- Use 'battles' when the question is mainly about:\n"
  "    * wars, battles, revolutions, uprisings, conflicts, invasions, sieges\n"
  "    * military participation, alliances in war, who fought whom\n"
  "  Examples (battles):\n"
  "    - 'In which wars did Portugal fight in the 19th century?'\n"
  "    - 'Que batalhas Portugal travou contra a Espanha?'\n"
  "    - 'Portuguese participation in World War I'\n"
  "\n"
  "IMPORTANT PRIORITY RULE:\n"
  "- If the question mentions both rulers and wars, choose based on the MAIN focus:\n"
  "    * If it asks WHO ruled / who was king / head of state -> 'monarchs'.\n"
  "    * If it asks ABOUT the conflict itself (which war, which battles, who fought) -> 'battles'.\n"
  "  Example: 'Who ruled Portugal during the Napoleonic Wars?' -> 'monarchs'.\n"
  "  Example: 'What battles did Portugal fight in the Napoleonic Wars?' -> 'battles'.\n"
  "\n"
  "Time rules:\n"
  "1. If the place is not explicitly specified but clearly implied, use 'Portugal' as target.\n"
  "2. Do NOT normalize 'relation'; keep the user's wording.\n"
  "3. If a specific year is mentioned, set both 'time.start' and 'time.end' to that year.\n"
  "4. If a range is mentioned (e.g. 'around 1830-1840'), set 'time.start' and 'time.end' accordingly.\n"
  "5. Always pick a single 'source_type' from ['monarchs', 'battles']; never use any other value.\n"
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