from functools import lru_cache
from typing import List, Dict

from langchain_community.vectorstores import InMemoryVectorStore
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings

from src.rag.csv_loader import multi_csv_to_docs
from src.common.utils import parse_year_safe, load_csv
from src.common.models import QueryPlan, CsvSourceConfig, RowData


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


# ------------

def build_source(configs: List[CsvSourceConfig]) -> Dict[str, List[RowData]]:
  source_data: Dict[str, List[RowData]] = {}
  for cfg in configs:
    source_data[cfg.name] = load_csv(cfg.path)
  return source_data


def filter_source_data(source_data: Dict[str, List[RowData]], plan: QueryPlan) -> List[RowData]:
  if plan.source_type is None or plan.source_type not in source_data:
    return []

  rows = source_data[plan.source_type]

  filtered_rows = []
  for row in rows:
    row_start = parse_year_safe(row.start_date)
    row_end = parse_year_safe(row.end_date)

    if plan.time.start is not None:
      start = plan.time.start
      end = plan.time.end or start

      if row_start is None or row_end is None:
        continue

      if row_end < start or row_start > end:
        continue

    filtered_rows.append(row)

  return filtered_rows
