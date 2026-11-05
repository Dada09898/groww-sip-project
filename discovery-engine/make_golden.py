"""Builds a 20-item golden set from YOUR REAL collected data (data/filtered.csv).
You then label the human_* columns yourself BEFORE looking at the AI tags.

python make_golden.py           # writes golden_set.csv (won't overwrite a labelled file)
python make_golden.py --force   # resample
"""
import os, sys
import pandas as pd
from config import DATA_DIR, BASE_DIR

OUT = os.path.join(BASE_DIR, "golden_set.csv")
TRIGGERS = ("returns_negative returns_unclear cash_crunch job_loss mandate_or_payment_failure "
            "app_bug app_confusion fund_doubt external_advice goal_changed trust_safety support_service other none")
ACTIONS = "started continuing considering_stop paused reduced skipped stopped blocked unknown"

def main(force=False):
    if os.path.exists(OUT) and not force:
        g = pd.read_csv(OUT)
        if g["human_trigger"].notna().any():
            sys.exit("golden_set.csv already has labels. Use --force to resample (you will lose them).")
    f = pd.read_csv(f"{DATA_DIR}/filtered.csv", low_memory=False)
    f = f[f["text"].str.split().str.len().between(8, 120)]   # readable length
    picks = []
    # 2 per non-Play source when available, so the set isn't 100% app reviews
    for src, g in f[f.source != "play_store"].groupby("source"):
        picks.append(g.sample(min(2, len(g)), random_state=7))
    taken = sum(len(p) for p in picks)
    play = f[f.source == "play_store"]
    need = 20 - taken
    low = play[play.rating <= 2].sample(min(len(play[play.rating <= 2]), round(need * 0.5)), random_state=7)
    mid = play[play.rating == 3].sample(min(len(play[play.rating == 3]), round(need * 0.2)), random_state=7)
    high = play[play.rating >= 4]
    high = high.sample(min(len(high), need - len(low) - len(mid)), random_state=7)
    g = pd.concat(picks + [low, mid, high]).head(20)
    g = g.assign(human_relevant="", human_trigger="", human_action="", notes="")
    cols = ["id", "source", "date", "rating", "url", "text",
            "human_relevant", "human_trigger", "human_action", "notes"]
    g.reindex(columns=cols).to_csv(OUT, index=False)
    print(f"Wrote {len(g)} REAL items to golden_set.csv  ({g.source.value_counts().to_dict()})")
    print("\nNow open it in Excel and fill, WITHOUT running the AI first:")
    print("  human_relevant: true / false")
    print(f"  human_trigger : {TRIGGERS}")
    print(f"  human_action  : {ACTIONS}")

if __name__ == "__main__":
    main(force="--force" in sys.argv)
