"""SAFE way to add hand-collected Reddit / social posts WITHOUT re-running collect.py
(collect.py with only some sources would overwrite raw.csv and filtered.csv).

1. Fill data/social_manual.csv (UTF-8) with columns: source,id,date,url,text
     source = reddit / x / linkedin / instagram / facebook
     id     = the post or comment id from the URL (any unique text is fine)
     text   = copy the post/comment exactly as written
2. python add_manual_sources.py
3. python tag.py --max-per-source 3000      (tags ONLY the new items)
4. python -u aggregate.py ; python evidence_log.py
Re-running this script is safe: rows already added are skipped.
"""
import os, sys
import pandas as pd
from config import DATA_DIR, STRONG_RX, MIN_WORDS

SRC = os.path.join(DATA_DIR, "social_manual.csv")

def relevant(t):
    t = str(t)
    return len(t.split()) >= MIN_WORDS and bool(STRONG_RX.search(t))

def main():
    if not os.path.exists(SRC):
        pd.DataFrame(columns=["source", "id", "date", "url", "text"]).to_csv(SRC, index=False)
        sys.exit("Created an empty data/social_manual.csv. Fill it, then run this again.")
    new = pd.read_csv(SRC, dtype=str).fillna("")
    need = {"source", "id", "url", "text"}
    if not need <= set(new.columns):
        sys.exit(f"social_manual.csv needs columns: source,id,date,url,text (found {list(new.columns)})")
    new = new[new["text"].str.strip() != ""].copy()
    new["source"] = new["source"].str.strip().str.lower()
    new["id"] = "so_" + new["id"].str.strip()
    new["rating"] = None
    if "date" not in new:
        new["date"] = ""
    no_url = (new["url"].str.strip() == "").sum()
    if no_url:
        print(f"WARNING: {no_url} rows have no URL. Add them: every item must be traceable.")
    new = new[["source", "id", "date", "rating", "text", "url"]].drop_duplicates("id")

    raw = pd.read_csv(f"{DATA_DIR}/raw.csv", low_memory=False)
    filt = pd.read_csv(f"{DATA_DIR}/filtered.csv", low_memory=False)
    add_raw = new[~new["id"].isin(raw["id"].astype(str)) & ~new["text"].isin(raw["text"])]
    raw = pd.concat([raw, add_raw], ignore_index=True)
    keep = add_raw.loc[add_raw["text"].map(relevant).astype(bool)].copy()
    keep["has_weak_term"] = False
    add_filt = keep[~keep["id"].isin(filt["id"].astype(str))]
    filt = pd.concat([filt, add_filt], ignore_index=True)        # appended at the END, so the
    raw.to_csv(f"{DATA_DIR}/raw.csv", index=False)                # existing tag sample is unchanged
    filt.to_csv(f"{DATA_DIR}/filtered.csv", index=False)

    vol = pd.DataFrame({"collected": raw.groupby("source").size(),
                        "sip_keyword_match": filt.groupby("source").size()}).fillna(0).astype(int)
    vol.loc["TOTAL"] = vol.sum()
    vol.to_csv(f"{DATA_DIR}/volume.csv")
    print(f"Added {len(add_raw)} new rows to raw.csv, {len(add_filt)} passed the SIP keyword filter.")
    dropped = len(add_raw) - len(keep)
    if dropped:
        print(f"{dropped} rows did not pass the filter (under {MIN_WORDS} words or no SIP/MF word).")
    print("\n", vol.to_string())
    print("\nNext: python tag.py --max-per-source 3000")

if __name__ == "__main__":
    main()
