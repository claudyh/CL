import pandas as pd

def store_triplets(res, file_path: str):
  """
  Expects SPARQL results where every binding has:
    ?subject, ?predicate, ?object, ?start_date, ?end_date
  (any of them may be missing/NULL)
  """
  rows = []

  for b in res["results"]["bindings"]:
    def val(name: str):
      return b.get(name, {}).get("value")

    subject = val("subject")
    predicate = val("predicate")
    obj = val("object")
    start = val("start_date")
    end = val("end_date")

    # Optional: strip time part if datetime
    if start:
      start = start.split("T")[0]
    if end:
      end = end.split("T")[0]

    rows.append(
      {
        "subject": subject,
        "predicate": predicate,
        "object": obj,
        "start_date": start,
        "end_date": end,
      }
    )

  df = pd.DataFrame(rows)
  df.to_csv(file_path, index=False)
  print(f"✅ Saved {len(df)} rows to {file_path}")