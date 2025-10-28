from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
import json, re
from typing import Dict, Any, Optional, List
from retrieve import retrieve

llm = ChatOllama(model="llama3.2:3b", temperature=0)

PLAN_PROMPT = ChatPromptTemplate.from_messages([
  SystemMessage(
    # Escape literal braces in JSON spec with double braces
    "You convert questions about Portugal's rulers into a strict JSON plan. "
    "Return ONLY JSON with keys exactly: "
    "{{\"target\": string, \"relation\": string, \"time_filter\": {{\"start\": int|null, \"end\": int|null}}}}. "
    "If the question contains a single year, set start=end=that year. "
    "If no year is present, set both to null. No text, only JSON."
  ),
  HumanMessage("{question}")
])

def normalize_keys(obj):
  if isinstance(obj, dict):
    out = {}
    for k, v in obj.items():
      nk = str(k).strip().strip('"').strip("'").lower()
      out[nk] = normalize_keys(v)
    return out
  if isinstance(obj, list):
    return [normalize_keys(x) for x in obj]
  return obj

def extract_year_from_text(text: str) -> Optional[int]:
    m = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", text)
    return int(m.group(0)) if m else None

def sanitize_plan(plan: Dict[str, Any], fallback_question: str) -> Dict[str, Any]:
    if not isinstance(plan, dict):
        plan = {}
    target = (plan.get("target") or plan.get("entity") or plan.get("subject") or "Portugal")
    relation = (plan.get("relation") or plan.get("rel") or "head of state")
    tf = plan.get("time_filter") or plan.get("time") or {}
    if isinstance(tf, dict):
        tf = normalize_keys(tf)
    start, end = tf.get("start"), tf.get("end")
    if start is None and end is None:
        yr = extract_year_from_text(fallback_question)
        if yr is not None:
            start = end = yr
    def to_int_or_none(v):
        try: return int(v)
        except Exception: return None
    start, end = to_int_or_none(start), to_int_or_none(end)
    return {"target": str(target), "relation": str(relation), "time_filter": {"start": start, "end": end}}

def parse_plan(question: str) -> Dict[str, Any]:
    msg = PLAN_PROMPT.format_messages(question=question)
    raw = llm.invoke(msg).content.strip()
    # optional: print raw for debugging
    # print("RAW LLM:", raw)
    if "```" in raw:
        parts = [p for p in raw.split("```") if "{" in p and "}" in p]
        raw = parts[0] if parts else raw.replace("```", "")
    try:
        plan = json.loads(raw)
        plan = normalize_keys(plan)
    except Exception:
        yr = extract_year_from_text(question)
        plan = {"target": "Portugal", "relation": "head of state", "time_filter": {"start": yr, "end": yr}}
    return sanitize_plan(plan, fallback_question=question)

def to_query_string(plan: Dict[str, Any]) -> str:
    tgt = plan.get("target") or ""
    rel = plan.get("relation") or ""
    tf = plan.get("time_filter") or {}
    s, e = tf.get("start"), tf.get("end")
    years = f" {'' if s is None else s}-{'' if e is None else e}" if (s is not None or e is not None) else ""
    return f"{tgt} {rel}{years}".strip()

def pick_year(tf: Dict[str, Any]) -> Optional[int]:
    if not isinstance(tf, dict): return None
    s, e = tf.get("start"), tf.get("end")
    return s if isinstance(s, int) and isinstance(e, int) and s == e else None

def metadatas_to_triples(metas: List[Dict[str, Any]]) -> Dict[str, Any]:
    triples, seen = [], set()
    for m in metas:
        key = (m.get("subject_label"), m.get("object_label"), m.get("start_year"), m.get("end_year"))
        if key in seen: continue
        seen.add(key)
        triples.append({
            "subject":   {"label": m.get("subject_label")},
            "predicate": {"label": m.get("predicate_label", "position held")},
            "object":    {"label": m.get("object_label")},
            "start_year": m.get("start_year"),
            "end_year":   m.get("end_year"),
            "source_uri": m.get("source_uri", "local:portuguese_monarchs.csv")
        })
    return {"triples": triples}

def answer(question: str) -> str:
    plan = parse_plan(question)
    query = to_query_string(plan)
    year_prefilter = pick_year(plan.get("time_filter", {}))
    metas, _docs = retrieve(query, year=year_prefilter, k=30)
    return json.dumps({"plan": plan, "results": metadatas_to_triples(metas)}, ensure_ascii=False, indent=2)

def main():
    for q in [
        "Who ruled Portugal in 1500?",
        "Who ruled Portugal in 1211?",
        "List rulers of Portugal around 1830-1840.",
        "Who was the head of state of Portugal?"
    ]:
      print(f"\nQ: {q}")
      print(answer(q))

if __name__ == "__main__":
    main()