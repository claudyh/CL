import traceback

from src.common.models import CsvSourceConfig
from src.rag.retriever import build_source, filter_source_data, build_vector_store
from src.agents.planner import parse_plan
from src.agents.answerer import answer_with_rag, answer


SOURCES = [
  CsvSourceConfig(
    name="monarchs",
    path="data/portuguese_monarchs.csv",
  ),
  CsvSourceConfig(
    name="battles",
    path="data/portuguese_battles.csv",
  ),
  # Add more sources as needed
]


USE_RAG = False


def main():
  if USE_RAG:
    vector_store = build_vector_store(SOURCES)
  else:
    source_data = build_source(SOURCES)

  # Some example questions
  questions = [
    "Who ruled Portugal in the year of 1500?",
    "Who ruled Portugal in 1211?",
    "List rulers of Portugal around 1830-1840.",
    "Who was the head of state of Portugal in 1910?",
    "Who was the prime minister of Portugal in 1980?",
    "In 1185 who was the king of Portugal?",
    "What battles took place between 1140 and 1144?",
  ]

  for q in questions:
    print("=" * 80)
    print(f"Q: {q}")
    try:
      plan = parse_plan(q)

      if USE_RAG:
        res = answer_with_rag(plan, q, vector_store)
      else:
        matches = filter_source_data(source_data, plan)
        res = answer(q, matches)

      print("\nAnswer:", res)
    except Exception as e:
      print("Error during answering:", e)
      traceback.print_exc()


if __name__ == "__main__":
  main()