"""Step 1+2: collect from all sources, de-duplicate, keyword-filter.
Each source is saved in data/sources/<name>.csv, so you can refresh ONE source
(python collect.py play) without losing or re-downloading the others.
Output: data/raw.csv, data/filtered.csv, data/volume.csv"""
import os, sys, pandas as pd
from config import DATA_DIR, STRONG_RX, WEAK_RX, MIN_WORDS
from scrapers import playstore, appstore, reddit, youtube, tradingqna, social_import

SOURCES = [("play", playstore), ("appstore", appstore), ("reddit", reddit),
           ("youtube", youtube), ("tradingqna", tradingqna), ("social", social_import)]

def is_sip_relevant(text):
    t = str(text)
    if len(t.split()) < MIN_WORDS:
        return False
    return bool(STRONG_RX.search(t))   # WEAK words alone never pass

SRC_DIR = os.path.join(DATA_DIR, "sources")
SOURCE_TO_CACHE = {"play_store": "play", "app_store": "appstore", "reddit": "reddit",
                   "reddit_comment": "reddit", "youtube": "youtube", "tradingqna": "tradingqna"}

def _seed_cache_from_raw():
    """First run of this version: split an existing raw.csv into per-source caches."""
    raw_path = os.path.join(DATA_DIR, "raw.csv")
    if os.path.isdir(SRC_DIR) or not os.path.exists(raw_path):
        return
    os.makedirs(SRC_DIR)
    raw = pd.read_csv(raw_path, low_memory=False)
    raw["_cache"] = raw["source"].map(SOURCE_TO_CACHE).fillna("social")
    for name, g in raw.groupby("_cache"):
        g.drop(columns="_cache").to_csv(os.path.join(SRC_DIR, f"{name}.csv"), index=False)
    print(f"Saved existing raw.csv as per-source caches: {sorted(raw['_cache'].unique())}")

def main(only=None):
    os.makedirs(DATA_DIR, exist_ok=True)
    _seed_cache_from_raw()
    os.makedirs(SRC_DIR, exist_ok=True)
    for name, mod in SOURCES:
        if only and name not in only:
            continue
        print(f"[{name}]")
        try:
            df = mod.fetch()
            print(f"  -> {len(df):,} items")
            if len(df):
                df.to_csv(os.path.join(SRC_DIR, f"{name}.csv"), index=False)
        except Exception as e:
            print(f"  -> FAILED: {e} (keeping previous data for this source, if any)")
    frames = []
    for name, _ in SOURCES:
        path = os.path.join(SRC_DIR, f"{name}.csv")
        if os.path.exists(path):
            frames.append(pd.read_csv(path, low_memory=False))
    if not frames:
        raise SystemExit("No data collected from any source.")
    raw = pd.concat(frames, ignore_index=True)
    if "url" not in raw:
        raw["url"] = ""
    raw["text"] = raw["text"].fillna("").astype(str).str.strip()
    raw = raw[raw["text"] != ""].drop_duplicates("id").drop_duplicates("text")
    raw.to_csv(f"{DATA_DIR}/raw.csv", index=False)

    filt = raw[raw["text"].apply(is_sip_relevant)].copy()
    filt["has_weak_term"] = filt["text"].str.contains(WEAK_RX)
    filt.to_csv(f"{DATA_DIR}/filtered.csv", index=False)

    vol = pd.DataFrame({"collected": raw.groupby("source").size(),
                        "sip_keyword_match": filt.groupby("source").size()}).fillna(0).astype(int)
    vol.loc["TOTAL"] = vol.sum()
    vol.to_csv(f"{DATA_DIR}/volume.csv")
    print("\nVOLUME (goes in the Evidence Log)\n", vol.to_string())

if __name__ == "__main__":
    # optional: python collect.py play youtube   -> refresh only those sources
    main(only=set(sys.argv[1:]) or None)
