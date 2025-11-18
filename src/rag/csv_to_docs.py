import pandas as pd
from datetime import datetime
from langchain_core.documents import Document
from src.common.models import CsvSourceConfig

def _parse_year_safe(date_str: str) -> int | None:
    if not isinstance(date_str, str):
        return None
    if len(date_str) >= 4 and date_str[:4].isdigit():
        return int(date_str[:4])
    return None

def csv_source_to_docs(cfg: CsvSourceConfig) -> list[Document]:
    df = pd.read_csv(cfg.path)

    docs: list[Document] = []

    for _, row in df.iterrows():
        subject = str(row[cfg.subject_col])
        predicate = str(row[cfg.predicate_col]) if cfg.predicate_col else ""
        obj = str(row[cfg.object_col]) if cfg.object_col else ""

        start_date = str(row[cfg.start_date_col]) if cfg.start_date_col else None
        end_date = str(row[cfg.end_date_col]) if cfg.end_date_col else None

        start_year = _parse_year_safe(start_date) if start_date else None
        end_year = _parse_year_safe(end_date) if end_date else None

        # Natural language summary for embeddings
        lines = [f"Source: {cfg.name}"]
        if cfg.name == "monarchs":
            lines.append(
                f"{subject} held position {obj} in Portugal "
                f"from {start_date} to {end_date}."
            )
            lines.append("This can be understood as a monarch or head of state.")
        else:
            # Generic fallback
            lines.append(f"{subject} {predicate} {obj}.")
            if start_date or end_date:
                lines.append(f"Relevant period: {start_date} to {end_date}.")

        text = "\n".join(lines)

        meta = {
            "source_type": cfg.name,
            "subject": subject,
            "predicate": predicate,
            "object": obj,
            "start_date": start_date,
            "end_date": end_date,
            "start_year": start_year,
            "end_year": end_year,
        }

        if cfg.extra_metadata:
            meta.update(cfg.extra_metadata)

        docs.append(Document(page_content=text, metadata=meta))

    print(f"[csv_to_docs] Built {len(docs)} docs from {cfg.name} ({cfg.path})")
    return docs


def multi_csv_to_docs(configs: list[CsvSourceConfig]) -> list[Document]:
    all_docs: list[Document] = []
    for cfg in configs:
        all_docs.extend(csv_source_to_docs(cfg))
    print(f"[csv_to_docs] Total docs from all CSVs: {len(all_docs)}")
    return all_docs