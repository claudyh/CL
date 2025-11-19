from langchain_community.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from src.common.utils import parse_year_safe
from src.rag.csv_loader import multi_csv_to_docs
from src.common.models import QueryPlan, CsvSourceConfig
from typing import List


def build_vector_store(csv_sources: List[CsvSourceConfig]):
  """
  Build an in-memory vector store from CSV sources.
  Uses OllamaEmbeddings + InMemoryVectorStore (fully local, no external DB).
  """
  docs = multi_csv_to_docs(csv_sources)
  store = InMemoryVectorStore.from_documents(
    docs,
    embedding=OllamaEmbeddings(model="llama3.1:8b")
  )
  return store


def retrieve_with_rag(plan: QueryPlan, store: InMemoryVectorStore, k=100) -> List[Document]:
  query = plan.as_query()
  docs = store.similarity_search(query, k=k)

  if plan.source_type:
    docs = [d for d in docs if d.metadata.get("source_type") == plan.source_type]

  if plan.time.start is not None:
    start = plan.time.start
    end = plan.time.end or start
    docs = [
      d for d in docs
      if isinstance(parse_year_safe(d.metadata.get("start_date")), int)
      and isinstance(parse_year_safe(d.metadata.get("end_date")), int)
      and not (parse_year_safe(d.metadata["end_date"]) < start or parse_year_safe(d.metadata["start_date"]) > end)
    ]

  return docs
