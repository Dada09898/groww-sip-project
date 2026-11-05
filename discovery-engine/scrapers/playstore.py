"""Play Store reviews.
1) Loads your downloaded export (config.PLAY_LOCAL_CSV) if present.
2) Tops it up with reviews newer than the export's last date, straight from Google Play."""
import os
import pandas as pd

TOPUP_MAX = int(os.getenv("PLAY_TOPUP_MAX", "150000"))
from config import PLAY_APP_ID, PLAY_LOCAL_CSV

def _from_local():
    if not os.path.exists(PLAY_LOCAL_CSV):
        print(f"  play: WARNING no local export at {PLAY_LOCAL_CSV}")
        print("  play: copy groww_reviews_last5y.csv into the data folder, then run: python collect.py play")
        return pd.DataFrame()
    df = pd.read_csv(PLAY_LOCAL_CSV, low_memory=False)
    out = pd.DataFrame({"source": "play_store", "id": df["reviewId"].astype(str),
                        "date": pd.to_datetime(df["at"], errors="coerce", utc=True),
                        "rating": df["score"], "text": df["content"].fillna("").astype(str)})
    print(f"  play: {len(out):,} reviews from local export "
          f"({out['date'].min():%Y-%m-%d} to {out['date'].max():%Y-%m-%d})")
    return out

def _scrape_newer(since, max_items=TOPUP_MAX):
    try:
        from google_play_scraper import reviews, Sort
    except ImportError:
        print("  play: google-play-scraper not installed, skipping top-up")
        return pd.DataFrame()
    rows, token = [], None
    while len(rows) < max_items:
        batch, token = reviews(PLAY_APP_ID, lang="en", country="in", sort=Sort.NEWEST,
                               count=200, continuation_token=token)
        if not batch:
            break
        rows.extend(batch)
        oldest = pd.Timestamp(batch[-1]["at"]).tz_localize("UTC")
        if since is not None and oldest <= since:
            break
        if token is None:
            break
    df = pd.DataFrame([{"source": "play_store", "id": str(r["reviewId"]),
                        "date": pd.Timestamp(r["at"]).tz_localize("UTC"),
                        "rating": r["score"], "text": r["content"] or ""} for r in rows])
    if since is not None and len(df):
        df = df[df["date"] > since]
    if len(df):
        print(f"  play: {len(df):,} newer reviews scraped "
              f"({df['date'].min():%Y-%m-%d} to {df['date'].max():%Y-%m-%d})")
        if since is not None and len(rows) >= max_items:
            print(f"  play: WARNING hit the {max_items:,} cap before reaching {since:%Y-%m-%d}; "
                  "set PLAY_TOPUP_MAX higher in .env to close the gap")
    else:
        print("  play: 0 newer reviews scraped")
    return df

def fetch():
    local = _from_local()
    since = local["date"].max() if len(local) else None
    try:
        newer = _scrape_newer(since)
    except Exception as e:   # network/blocked: keep the local export
        print(f"  play: top-up failed ({e}), using local export only")
        newer = pd.DataFrame()
    df = pd.concat([local, newer], ignore_index=True).drop_duplicates("id")
    df["date"] = df["date"].astype(str)
    return df
