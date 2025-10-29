import pandas as pd

def store_triplets(res, file_path):
    
    # Store triplets with temporal qualifiers
    rows = []
    
    for b in res["results"]["bindings"]:
        
        subject = b["personLabel"]["value"]
        predicate = 'heldPosition'
        obj = b["positionLabel"]["value"]
        start = b.get("start", {}).get("value")
        end = b.get("end", {}).get("value")
        
        rows.append({
        'subject': subject,
        'predicate': predicate,
        'object': obj,
        'start_date': start.split("T")[0],
        'end_date': end.split("T")[0]
        })
    
    # Save dataset
    df= pd.DataFrame(rows)
    df.to_csv(file_path, index=False)
