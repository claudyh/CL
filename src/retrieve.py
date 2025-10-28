# src/retrieve.py
# pip install chromadb sentence-transformers

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = "storage/chroma_db"
COLLECTION = "pt_monarchs"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

client = chromadb.PersistentClient(path=CHROMA_DIR)
col = client.get_or_create_collection(COLLECTION)
model = SentenceTransformer(EMBED_MODEL)

def _overlaps(meta, year: int | None) -> bool:
    if year is None:
        return True
    sy = meta.get("start_year")
    ey = meta.get("end_year")  # may be None (open interval)
    left_ok = (sy is None) or (sy <= year)
    right_ok = (ey is None) or (ey >= year)
    return bool(left_ok and right_ok)

def retrieve(question: str, year: int | None = None, k: int = 20):
    qemb = model.encode([question], normalize_embeddings=True).tolist()[0]

    # Build a safe 'where' clause. Use only start_year <= year here.
    # (We’ll finish the end_year check in Python to handle None/open intervals.)
    where = None
    if year is not None:
      where = {
        "start_year": {"$lte": year}
      }

    res = col.query(
      query_embeddings=[qemb],
      n_results=k * 3,          # overfetch, we'll post-filter/dedupe
      where=where
    )

    # Post-filter by end_year overlap and dedupe
    metas = res.get("metadatas", [[]])[0]
    docs = res.get("documents", [[]])[0]

    filtered = []
    seen = set()
    for m, d in zip(metas, docs):
        if not _overlaps(m, year):
            continue
        key = (m.get("subject_label"), m.get("object_label"),
               m.get("start_year"), m.get("end_year"))
        if key in seen:
            continue
        seen.add(key)
        filtered.append((m, d))

    # Return up to k results
    filtered = filtered[:k]
    return [m for m, _ in filtered], [d for _, d in filtered]