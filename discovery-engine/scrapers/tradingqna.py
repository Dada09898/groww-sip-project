"""TradingQ&A (Zerodha's Discourse forum). Search finds topics, then full posts are fetched
from each topic (search alone only returns short snippets)."""
import re, time, html, requests, pandas as pd
from config import TRADINGQNA_QUERIES

HEADERS = {"User-Agent": "sip-discovery-research/1.1 (student project)"}
BASE = "https://tradingqna.com"

def _clean(cooked):
    return html.unescape(re.sub(r"<[^>]+>", " ", cooked or "")).strip()

def fetch(max_topics_per_query=15, posts_per_topic=20):
    topic_ids, rows, seen = [], [], set()
    for q in TRADINGQNA_QUERIES:
        r = requests.get(f"{BASE}/search.json", params={"q": q}, headers=HEADERS, timeout=20)
        time.sleep(2)
        if r.status_code != 200:
            continue
        for t in r.json().get("topics", [])[:max_topics_per_query]:
            if t["id"] not in topic_ids:
                topic_ids.append(t["id"])
    for tid in topic_ids:
        r = requests.get(f"{BASE}/t/{tid}.json", headers=HEADERS, timeout=20)
        time.sleep(1.5)
        if r.status_code != 200:
            continue
        js = r.json()
        title = js.get("title", "")
        for p in js.get("post_stream", {}).get("posts", [])[:posts_per_topic]:
            if p["id"] in seen:
                continue
            seen.add(p["id"])
            body = _clean(p.get("cooked"))
            text = f"{title}. {body}" if p.get("post_number") == 1 else body
            rows.append({"source": "tradingqna", "id": f"tq_{p['id']}", "date": p.get("created_at"),
                         "rating": None, "text": text, "url": f"{BASE}/t/{tid}/{p.get('post_number', 1)}"})
    return pd.DataFrame(rows)
