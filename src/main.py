import os
import traceback
from typing import List

from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage

from langchain_ollama import ChatOllama, OllamaEmbeddings

from graph_retriever.strategies import Eager
from langchain_graph_retriever import GraphRetriever
from langchain_community.vectorstores import InMemoryVectorStore

from src.common.models import QueryPlan, CsvSourceConfig
from src.rag import multi_csv_to_docs

# ---------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------

# LLM that will produce QueryPlan and also answer with RAG
planner_llm = ChatOllama(
  model="llama3.1:8b",
  temperature=0,
)
llm_structured = planner_llm.with_structured_output(schema=QueryPlan)

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

def parse_plan(question: str) -> QueryPlan:
  messages = [
    PLANNER_SYSTEM_PROMPT,
    HumanMessage(content=question),
  ]
  return llm_structured.invoke(messages)


SOURCES = [
  CsvSourceConfig(
    name="monarchs",
    path="data/portuguese_monarchs.csv",
    subject_col="subject",
    predicate_col="predicate",
    object_col="object",
    start_date_col="start_date",
    end_date_col="end_date",
    extra_metadata={"country": "Portugal"},
  ),
  # Add more sources as needed
]


# ---------------------------------------------------------------------
# 3. Create vector store + GraphRetriever (Graph RAG)
# ---------------------------------------------------------------------

def build_vector_store(configs: List[CsvSourceConfig]) -> InMemoryVectorStore:
  """
  Build an in-memory vector store from Documents.
  Uses OllamaEmbeddings + InMemoryVectorStore (fully local, no external DB).
  """
  docs = multi_csv_to_docs(configs)

  vector_store = InMemoryVectorStore.from_documents(
    documents=docs,
    embedding=OllamaEmbeddings(model="llama3.1:8b"),
  )
  print("Vector store created and populated.")
  return vector_store


def build_graph_retriever(vector_store: InMemoryVectorStore) -> GraphRetriever:
  """al
  GraphRetriever configuration:

  - store: the provided vector_store
  - edges: connect docs where a 'mentions' value on one side matches 'uri' on the other.
  - strategy: Eager BFS-like traversal.
  """
  retriever = GraphRetriever(
    store=vector_store,
    edges=[("mentions", "uri")],
    strategy=Eager(start_k=32, k=40, max_depth=1),
  )
  print("GraphRetriever initialized.")
  return retriever


# ---------------------------------------------------------------------
# 4. Turn QueryPlan into a text query for Graph RAG
# ---------------------------------------------------------------------


def retrieve_with_rag(plan: QueryPlan, vector_store: InMemoryVectorStore, k: int = 100) -> List[Document]:
  query = plan.as_query()

  docs = vector_store.similarity_search(query, k=k)

  if plan.source_type: # Filter by source_type if specified
    docs = [
      d for d in docs
      if d.metadata.get("source_type") == plan.source_type
    ]
    print(f"{len(docs)} documents after source_type filtering")

  if plan.time.start is not None or plan.time.end is not None:
    start_year = plan.time.start
    end_year = plan.time.end or plan.time.start

    filtered = []
    for d in docs:
      s = d.metadata.get("start_year")
      e = d.metadata.get("end_year")
      if isinstance(s, int) and isinstance(e, int):
        # keep if [s, e] overlaps [start_year, end_year]
        if not (e < start_year or s > end_year):
          filtered.append(d)

    docs = filtered
    print(f"{len(docs)} documents after year filtering")

  print(f"Retrieved {len(docs)} documents for query: {query}")
  return docs


# ---------------------------------------------------------------------
# 5. Final answer step: LLM + Graph RAG context
# ---------------------------------------------------------------------

answer_llm = ChatOllama(model="llama3.1:8b")

ANSWER_SYSTEM_PROMPT = SystemMessage(
  "You answer questions about historical facts involving Portugal using ONLY the context provided.\n\n"
  "The context contains rows derived from CSV files. Each row describes a tenure, with:\n"
  "- subject: the person (e.g. 'Manuel I of Portugal')\n"
  "- predicate: typically 'heldPosition'\n"
  "- object: the role (e.g. 'Monarch of Portugal')\n"
  "- start_date: the start date of the tenure\n"
  "- end_date: the end date of the tenure\n\n"
  "Very important rules:\n"
  "1. A tenure MATCHES a question about a specific year Y if Y is between start_date and end_date (inclusive).\n"
  "2. A tenure MATCHES a question about a range of years [A, B] if its period overlaps that range.\n"
  "3. You ARE allowed to do simple date reasoning (checking if a year falls between two years).\n"
  "4. You MUST NOT invent people, dates, or roles that are not present in the context.\n"
  "5. When you answer, you MUST output one CSV line per matching tenure, using EXACTLY this format:\n"
  "   subject,predicate,object,start_date,end_date\n"
  "   If multiple tenures match, output multiple lines, one per line.\n"
  "6. If no tenures match the question based on the context, answer with exactly:\n"
  "   NOT_SURE\n"
)

def answer_with_rag(question: str, vector_store: InMemoryVectorStore) -> str:
  # 1) Plan
  plan = parse_plan(question)
  print(f"QueryPlan: {plan}\n")

  # 2) Retrieve context
  docs = retrieve_with_rag(plan, vector_store)

  if not docs:
    context = "NO_RELEVANT_CONTEXT"
  else:
    context_parts = []
    for i, d in enumerate(docs):
      context_parts.append(
        f"--- Document {i+1} ---\n"
        f"Source type: {d.metadata.get('source_type')}\n"
        f"Subject: {d.metadata.get('subject')}\n"
        f"Predicate: {d.metadata.get('predicate')}\n"
        f"Object: {d.metadata.get('object')}\n"
        f"Start date: {d.metadata.get('start_date')}\n"
        f"End date: {d.metadata.get('end_date')}\n\n"
        f"{d.page_content}"
      )
    context = "\n\n".join(context_parts)

  messages = [
    ANSWER_SYSTEM_PROMPT,
    HumanMessage(
      content=(
        f"Question: {question}\n\n"
        f"Structured plan (you may use it, but it might contain mistakes): {plan.model_dump()}\n\n"
        f"Context (rows from the CSV-derived documents):\n{context}\n\n"
        "From this context, identify all tenures that match the question "
        "according to the rules. Remember to output either one or more CSV lines "
        "in the exact format 'subject,predicate,object,start_date,end_date', or "
        "NOT_SURE if nothing matches."
      )
    ),
  ]

  response = answer_llm.invoke(messages)
  return response.content


# ---------------------------------------------------------------------
# 6. CLI / demo
# ---------------------------------------------------------------------

def main():
  vector_store = build_vector_store(SOURCES)

  # Some example questions
  questions = [
    "Who ruled Portugal in the year of 1500?",
    "Who ruled Portugal in 1211?",
    "List rulers of Portugal around 1830-1840.",
    "Who was the head of state of Portugal in 1910?",
    "Who was the prime minister of Portugal in 1980?",
    "In 1185 who was the king of Portugal?",
  ]

  for q in questions:
    print("=" * 80)
    print(f"Q: {q}")
    try:
      answer = answer_with_rag(q, vector_store)
      print("\nAnswer:", answer)
    except Exception as e:
      print("Error during answering:", e)
      traceback.print_exc()


if __name__ == "__main__":
  main()