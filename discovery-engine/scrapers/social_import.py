"""Social media (X/Twitter, Instagram, LinkedIn, Facebook groups). Their APIs are paid or closed,
so copy real posts by hand into data/social_manual.csv with columns:
source,id,date,url,text
Keep the url so every item can be traced back to where you found it."""
import os, pandas as pd
from config import DATA_DIR

def fetch():
    p = os.path.join(DATA_DIR, "social_manual.csv")
    if not os.path.exists(p):
        print("  social: skipped, add data/social_manual.csv")
        return pd.DataFrame()
    df = pd.read_csv(p)
    df["rating"] = None
    if "url" not in df:
        df["url"] = ""
    df["id"] = "so_" + df["id"].astype(str)
    return df[["source", "id", "date", "rating", "text", "url"]]
