"""Reddit posts + comments from Indian investing subreddits.
Uses PRAW (official API) when REDDIT_CLIENT_ID/SECRET are set, which is far more reliable.
Falls back to the public JSON endpoints, which Reddit often blocks (403/429)."""
import time, requests, pandas as pd
from config import SUBREDDITS, REDDIT_QUERIES, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET

UA = "sip-discovery-research/1.1 (student research project)"

def _row(src, id_, date, text, url=""):
    return {"source": src, "id": f"rd_{id_}", "date": date, "rating": None, "text": text, "url": url}

def _fetch_praw(limit_per_query, comments_per_post):
    import praw
    r = praw.Reddit(client_id=REDDIT_CLIENT_ID, client_secret=REDDIT_CLIENT_SECRET, user_agent=UA)
    rows, seen = [], set()
    for sub in SUBREDDITS:
        for q in REDDIT_QUERIES:
            try:
                results = list(r.subreddit(sub).search(q, sort="relevance", time_filter="all",
                                                       limit=limit_per_query))
            except Exception as e:
                print(f"  reddit r/{sub} '{q}': {e}")
                continue
            for s in results:
                if s.id in seen:
                    continue
                seen.add(s.id)
                rows.append(_row("reddit", s.id, s.created_utc, f"{s.title}. {s.selftext}",
                                 f"https://reddit.com{s.permalink}"))
                s.comments.replace_more(limit=0)
                for c in s.comments.list()[:comments_per_post]:
                    if c.id not in seen and getattr(c, "body", ""):
                        seen.add(c.id)
                        rows.append(_row("reddit_comment", c.id, c.created_utc, c.body,
                                         f"https://reddit.com{c.permalink}"))
    return rows

def _get(url, params=None):
    r = requests.get(url, params=params, headers={"User-Agent": UA}, timeout=20)
    time.sleep(2)
    if r.status_code in (403, 429):
        raise PermissionError(f"Reddit returned {r.status_code}. Add REDDIT_CLIENT_ID/SECRET to .env")
    return r.json() if r.status_code == 200 else {}

def _fetch_public(limit_per_query, comments_per_post):
    rows, seen = [], set()
    for sub in SUBREDDITS:
        for q in REDDIT_QUERIES:
            js = _get(f"https://www.reddit.com/r/{sub}/search.json",
                      {"q": q, "restrict_sr": 1, "sort": "relevance", "t": "all",
                       "limit": limit_per_query})
            for c in js.get("data", {}).get("children", []):
                d = c["data"]
                if d["id"] in seen:
                    continue
                seen.add(d["id"])
                rows.append(_row("reddit", d["id"], d["created_utc"],
                                 f'{d["title"]}. {d.get("selftext", "")}',
                                 f'https://reddit.com{d["permalink"]}'))
                cj = _get(f'https://www.reddit.com{d["permalink"]}.json', {"limit": comments_per_post})
                if isinstance(cj, list) and len(cj) > 1:
                    for cm in cj[1]["data"]["children"]:
                        cd = cm.get("data", {})
                        if cd.get("body") and cd["id"] not in seen:
                            seen.add(cd["id"])
                            rows.append(_row("reddit_comment", cd["id"], cd.get("created_utc"),
                                             cd["body"], f'https://reddit.com{cd.get("permalink", "")}'))
    return rows

def fetch(limit_per_query=25, comments_per_post=30):
    if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
        rows = _fetch_praw(limit_per_query, comments_per_post)
    else:
        print("  reddit: skipped. Reddit closed new API keys (Nov 2025) and logged-out access.")
        print("  reddit: add Reddit posts by hand to data/social_manual.csv (source=reddit)")
        return pd.DataFrame()
    return pd.DataFrame(rows)
