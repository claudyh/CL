import requests
from requests.exceptions import RequestException, JSONDecodeError

WIKIDATA_SEARCH_URL = "https://www.wikidata.org/w/api.php"
SPARQL_URL = "https://query.wikidata.org/sparql"

# use a session with a proper User-Agent (include contact if possible)
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "CL-project/0.1 (mailto:your-email@example.com)",
    "Accept": "application/json"
})

def get_wikidata_id(label, entity_type="item"):
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "language": "en",
        "search": label,
        "type": entity_type
    }
    try:
        resp = SESSION.get(WIKIDATA_SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        # be safe: ensure returned content is JSON
        if "application/json" not in resp.headers.get("Content-Type", ""):
            print("❌ Unexpected content-type:", resp.headers.get("Content-Type"))
            return None
        data = resp.json()
    except (RequestException, JSONDecodeError) as e:
        print("❌ Request error:", str(e))
        return None

    if data.get("search"):
        return data["search"][0]["id"]
    return None

def query_triples(subject_id, predicate_id):
    query = f"""
    SELECT ?object ?objectLabel WHERE {{
        wd:{subject_id} wdt:{predicate_id} ?object .
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
    }}
    """
    headers = {"Accept": "application/sparql-results+json", "User-Agent": SESSION.headers["User-Agent"]}
    try:
        resp = SESSION.get(SPARQL_URL, params={"query": query, "format": "json"}, headers=headers, timeout=15)
        resp.raise_for_status()
        if "application/sparql-results+json" not in resp.headers.get("Content-Type", "") and "application/json" not in resp.headers.get("Content-Type", ""):
            print("❌ Unexpected content-type from SPARQL:", resp.headers.get("Content-Type"))
            return []
        data = resp.json()
    except (RequestException, JSONDecodeError) as e:
        print("❌ SPARQL request error:", str(e))
        return []

    return data["results"]["bindings"]

def main():
    subject_label = input("Enter subject (e.g., 'Earth'): ")
    predicate_label = input("Enter predicate (e.g., 'shape'): ")

    print("\nSearching Wikidata IDs...")
    subject_id = get_wikidata_id(subject_label, "item")
    predicate_id = get_wikidata_id(predicate_label, "property")

    if not subject_id:
        print(f"❌ No Wikidata item found for subject '{subject_label}'")
        return
    if not predicate_id:
        print(f"❌ No Wikidata property found for predicate '{predicate_label}'")
        return

    print(f"✅ Found Subject: {subject_label} → {subject_id}")
    print(f"✅ Found Predicate: {predicate_label} → {predicate_id}")

    print("\nFetching triples from Wikidata...")
    results = query_triples(subject_id, predicate_id)

    if not results:
        print("❌ No data found for this subject-predicate pair.")
    else:
        print("\n✔ Triples found:")
        for r in results:
            obj = r["object"]["value"].split("/")[-1]
            obj_label = r["objectLabel"]["value"]
            print(f"({subject_label}, {predicate_label}, {obj_label})  → wd:{obj}")


if __name__ == "__main__":
    main()