from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import MessagesState
from common.query_plan import QueryPlan
# from retrieve import retrieve_text

from dotenv import load_dotenv
load_dotenv()


llm = ChatOllama(
  model="llama3.1:8b",
  validate_model_on_init=True,
  temperature=0,
)

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
    plan = parse_plan(q)
    print("Plan:", plan)
    # print(retrieve_text(plan))

if __name__ == "__main__":
  main()