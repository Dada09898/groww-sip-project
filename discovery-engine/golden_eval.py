"""Step 6: compare AI tags with YOUR hand labels in golden_set.csv.
Relevance is scored on all 20 items; trigger and action only on items you marked relevant."""
import os, sys
import pandas as pd
from config import BASE_DIR, DATA_DIR
from tagger import tag_text

def norm(x):
    return str(x).strip().lower()

def main(label=""):
    """label (optional) also saves a versioned copy, e.g. golden_results_v3.csv,
    so you can compare prompt versions in the Evidence Log."""
    path = os.path.join(BASE_DIR, "golden_set.csv")
    if not os.path.exists(path):
        sys.exit("No golden_set.csv. Run: python make_golden.py, then label it by hand.")
    g = pd.read_csv(path)
    if g["human_relevant"].isna().any() or (g["human_relevant"].astype(str).str.strip() == "").any():
        sys.exit("Fill human_relevant / human_trigger / human_action for every row first.")
    rows = []
    for _, r in g.iterrows():
        ai = tag_text(r["text"])
        rows.append({"id": r["id"], "source": r["source"], "text": str(r["text"])[:160],
                     "human_relevant": r["human_relevant"], "ai_relevant": ai.get("relevant"),
                     "human_trigger": r["human_trigger"], "ai_trigger": ai.get("trigger"),
                     "human_action": r["human_action"], "ai_action": ai.get("action"),
                     "ai_quote": ai.get("quote"), "ai_confidence": ai.get("confidence"),
                     "ai_error": ai.get("error", "")})
    out = pd.DataFrame(rows)
    for f in ["relevant", "trigger", "action"]:
        out[f"agree_{f}"] = out[f"human_{f}"].map(norm) == out[f"ai_{f}"].map(norm)
    is_rel = out["human_relevant"].map(norm) == "true"
    summary = {
        "relevant": (out["agree_relevant"].mean(), len(out)),
        "trigger": (out.loc[is_rel, "agree_trigger"].mean(), int(is_rel.sum())),
        "action": (out.loc[is_rel, "agree_action"].mean(), int(is_rel.sum())),
    }
    os.makedirs(DATA_DIR, exist_ok=True)
    out.to_csv(os.path.join(DATA_DIR, "golden_results.csv"), index=False)
    pd.DataFrame([{"field": k, "agreement_pct": round(100 * v[0]), "n": v[1]}
                  for k, v in summary.items()]).to_csv(os.path.join(DATA_DIR, "golden_summary.csv"), index=False)
    if label:
        out.to_csv(os.path.join(DATA_DIR, f"golden_results_{label}.csv"), index=False)
        pd.read_csv(os.path.join(DATA_DIR, "golden_summary.csv")).to_csv(
            os.path.join(DATA_DIR, f"golden_summary_{label}.csv"), index=False)
    for k, (acc, n) in summary.items():
        print(f"{k:9s} agreement: {100*acc:.0f}%  (n={n})")
    bad = out[~out.agree_relevant | (is_rel & ~(out.agree_trigger & out.agree_action))]
    print("\nDisagreements (copy the interesting ones into data/corrections.csv):")
    print(bad[["id", "text", "human_trigger", "ai_trigger", "human_action", "ai_action"]].to_string())

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
