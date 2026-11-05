"""Groww App Store reviews via Apple's public RSS feed.
Apple only exposes the ~500 most recent reviews per country, so this source is small."""
import time, requests, pandas as pd
from config import APPSTORE_APP_ID

def fetch(pages=10, country="in"):
    rows = []
    for p in range(1, pages + 1):
        url = (f"https://itunes.apple.com/{country}/rss/customerreviews/page={p}"
               f"/id={APPSTORE_APP_ID}/sortby=mostrecent/json")
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            break
        entries = r.json().get("feed", {}).get("entry", [])
        if isinstance(entries, dict):
            entries = [entries]
        if not entries:
            break
        for e in entries:
            if "content" not in e or "im:rating" not in e:
                continue
            rows.append({"source": "app_store", "id": "as_" + e["id"]["label"],
                         "date": e["updated"]["label"], "rating": int(e["im:rating"]["label"]),
                         "text": e["title"]["label"] + ". " + e["content"]["label"]})
        time.sleep(1)
    return pd.DataFrame(rows)
