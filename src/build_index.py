# pip install pandas chromadb sentence-transformers

import os, json, hashlib
import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb

DATA_CSV = "data/portuguese_monarchs.csv"  # columns: person, position, start, end
CHROMA_DIR = "storage/chroma_db"
CACHE_MANIFEST = "storage/cache/pt_monarchs.manifest.json"
COLLECTION = "pt_monarchs"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # local, fast

os.makedirs(os.path.dirname(CHROMA_DIR), exist_ok=True)
os.makedirs(os.path.dirname(CACHE_MANIFEST), exist_ok=True)

def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def normalize_year(s: str | None):
    if not s or not isinstance(s, str):
        return None
    # expect ISO like 1495-10-25T... or just 1495-01-01...
    try:
        return int(s[:4])
    except Exception:
        return None

def row_id(person: str, position: str, start_y, end_y) -> str:
    key = f"{person}|{position}|{start_y}|{end_y}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()

def text_for_embedding(person: str, position: str, sy, ey) -> str:
    years = ""
    if sy or ey:
        years = f" {sy if sy else ''}-{ey if ey else ''}"
    return f"{person} [position held] {position}{years}"

def load_manifest() -> dict:
    if os.path.exists(CACHE_MANIFEST):
        with open(CACHE_MANIFEST, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"file_hash": "", "ids": []}

def save_manifest(m: dict):
    with open(CACHE_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=2)

def main():
    if not os.path.exists(DATA_CSV):
        raise FileNotFoundError(f"Missing {DATA_CSV}")

    # 1) Skip if file unchanged
    curr_hash = file_sha256(DATA_CSV)
    manifest = load_manifest()
    if manifest.get("file_hash") == curr_hash:
        print("No changes detected in CSV. Skipping embedding.")
        return

    # 2) Load and normalize
    df = pd.read_csv(DATA_CSV)
    required = {"person", "position", "start", "end"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {missing}")

    df["start_year"] = df["start"].map(normalize_year)
    df["end_year"] = df["end"].map(normalize_year)
    df["doc_id"] = [
        row_id(p, o, sy, ey)
        for p, o, sy, ey in zip(df["person"], df["position"], df["start_year"], df["end_year"])
    ]

    # 3) Connect Chroma
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    col = client.get_or_create_collection(COLLECTION)

    prev_ids = set(manifest.get("ids", []))
    curr_ids = set(df["doc_id"].tolist())
    to_add = curr_ids - prev_ids
    to_delete = prev_ids - curr_ids

    if to_delete:
        col.delete(ids=list(to_delete))
        print(f"Deleted {len(to_delete)} removed triples from index.")

    if to_add:
        add_df = df[df["doc_id"].isin(to_add)].copy()
        texts = [text_for_embedding(r.person, r.position, r.start_year, r.end_year) for _, r in add_df.iterrows()]
        metas = []
        for _, r in add_df.iterrows():
            metas.append({
                # Minimal “extended triple” metadata
                "subject_label": r.person,
                "predicate_label": "position held",
                "object_label": r.position,
                "start_year": int(r.start_year) if pd.notna(r.start_year) else None,
                "end_year": int(r.end_year) if pd.notna(r.end_year) else None,
                "source_uri": "local:portuguese_monarchs.csv"
            })

        model = SentenceTransformer(EMBED_MODEL)
        embs = model.encode(texts, normalize_embeddings=True).tolist()
        col.add(ids=add_df["doc_id"].tolist(), documents=texts, embeddings=embs, metadatas=metas)
        print(f"Added {len(add_df)} new/changed triples to index.")

    # 4) Save manifest
    save_manifest({"file_hash": curr_hash, "ids": list(curr_ids)})
    print("Index up to date.")

if __name__ == "__main__":
    main()