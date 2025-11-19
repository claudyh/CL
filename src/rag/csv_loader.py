from langchain_core.documents import Document

from src.common.models import CsvSourceConfig
from src.common.utils import load_csv

def csv_source_to_docs(cfg: CsvSourceConfig) -> list[Document]:
  rows = load_csv(cfg.path)

  docs: list[Document] = []

  for row in rows:
    # Natural language summary for embeddings
    lines = [f"Source: {cfg.name}"]
    if cfg.name == "monarchs":
      lines.append(
        f"{row.subject} held position {row.object} in Portugal "
        f"from {row.start_date} to {row.end_date}."
      )
      lines.append("This can be understood as a monarch or head of state.")
    else:
      # Generic fallback
      lines.append(f"{row.subject} {row.predicate} {row.object}.")
      if row.start_date or row.end_date:
        lines.append(f"Relevant period: {row.start_date} to {row.end_date}.")

    text = "\n".join(lines)

    meta = row.model_dump()
    meta["source_type"] = cfg.name
    docs.append(Document(page_content=text, metadata=meta))

  print(f"[csv_to_docs] Built {len(docs)} docs from {cfg.name} ({cfg.path})")
  return docs


def multi_csv_to_docs(configs: list[CsvSourceConfig]) -> list[Document]:
  all_docs: list[Document] = []
  for cfg in configs:
    all_docs.extend(csv_source_to_docs(cfg))
  print(f"[csv_to_docs] Total docs from all CSVs: {len(all_docs)}")
  return all_docs