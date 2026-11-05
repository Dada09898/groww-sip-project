"""Builds the AI Evidence Log (PDF deliverable) as data/Evidence_Log.md.
Write your 2-3 corrections in data/corrections.csv with columns:
item_id,ai_output,corrected_to,why
Then paste Evidence_Log.md into a Google Doc set to 'Anyone with the link can view'.

v2 of this script: one-line text in tables, agreement recomputed from the labels,
your golden-set notes shown, prompt-version history, sampling + coverage notes."""
import os, glob
from datetime import date
import pandas as pd
from config import (DATA_DIR, BASE_DIR, TAG_MODEL, SYNTH_MODEL, LLM_PROVIDER,
                    GEMINI_TAG_MODEL, GEMINI_SYNTH_MODEL)

PDF_SOURCES = {"Play Store": lambda s: s == "play_store", "App Store": lambda s: s == "app_store",
               "Reddit": lambda s: "reddit" in s, "TradingQ&A": lambda s: "tradingqna" in s,
               "YouTube": lambda s: s == "youtube"}

def load(n, base=DATA_DIR):
    p = os.path.join(base, n)
    return pd.read_csv(p, low_memory=False) if os.path.exists(p) else None

def md(df, index=True):
    return df.to_markdown(index=index) if df is not None and len(df) else "_not generated yet_"

def one_line(s, n=160):
    s = " ".join(str(s).split())          # removes line breaks that break markdown tables
    return s if len(s) <= n else s[:n - 1] + "…"

def norm(x):
    x = str(x).strip().lower()
    return "" if x == "nan" else x

def main():
    vol, tag = load("volume.csv"), load("tagged.csv")
    gold, gsum, corr = load("golden_results.csv"), load("golden_summary.csv"), load("corrections.csv")
    gset = load("golden_set.csv", BASE_DIR)
    tag_model = GEMINI_TAG_MODEL if LLM_PROVIDER == "gemini" else TAG_MODEL
    syn_model = GEMINI_SYNTH_MODEL if LLM_PROVIDER == "gemini" else SYNTH_MODEL
    out = ["# AI Evidence Log: Groww first-time SIP continuation discovery engine\n",
           f"_Generated {date.today()} | provider: {LLM_PROVIDER} | tagging model: {tag_model} | "
           f"synthesis model: {syn_model}_\n",
           "## 1. Sources and volume analysed\n"]
    if vol is not None:
        vol = vol.set_index(vol.columns[0])
        if tag is not None:
            rel = tag[tag["relevant"].astype(str).str.lower() == "true"]
            vol["llm_tagged"] = tag.groupby("source").size()
            vol["llm_relevant"] = rel.groupby("source").size()
            vol.loc["TOTAL", ["llm_tagged", "llm_relevant"]] = [len(tag), len(rel)]
        out.append(md(vol.fillna(0).astype(int)))
        out.append("\n**Pipeline:** collect -> keyword filter (SIP/MF terms, at least 6 words) -> LLM "
                   "tagging with a fixed schema (15 items per request) -> counts, segment cross-tabs, "
                   "opportunity scoring -> LLM synthesis.\n")
        notes = []
        if "sip_keyword_match" in vol and "llm_tagged" in vol:
            for s, r in vol.drop("TOTAL", errors="ignore").iterrows():
                if r["sip_keyword_match"] > r.get("llm_tagged", 0) > 0:
                    notes.append(f"{s}: a random sample of {int(r['llm_tagged']):,} of "
                                 f"{int(r['sip_keyword_match']):,} keyword matches was tagged "
                                 "(seed 42, to fit the free API quota).")
        if tag is not None:
            notes.append(f"Overall {len(rel):,} of {len(tag):,} tagged items "
                         f"({100 * len(rel) / max(len(tag), 1):.0f}%) were SIP-relevant.")
        errs = load("tag_errors.csv")
        notes.append(f"Items that could not be tagged in the last run: {0 if errs is None else len(errs)}.")
        srcs = [s for s in vol.index if s != "TOTAL"]
        gaps = [n for n, t in PDF_SOURCES.items() if not any(t(s) for s in srcs)]
        if gaps:
            notes.append(f"**Not covered:** {', '.join(gaps)}.")
        notes.append("App-store reviews over-represent technical complaints; community sources "
                     "(TradingQ&A, YouTube) carry more of the 'should I continue' questions.")
        out.append("**Coverage notes**\n\n" + "\n".join(f"- {n}" for n in notes))

    out.append("\n\n## 2. Golden set: 20 real items labelled by hand\n")
    if gold is not None:
        g = gold.copy()
        for f in ["relevant", "trigger", "action"]:
            g[f"human_{f}"] = g[f"human_{f}"].map(norm)
            g[f"ai_{f}"] = g[f"ai_{f}"].map(norm)
            g[f"agree_{f}"] = g[f"human_{f}"] == g[f"ai_{f}"]
        rel = g["human_relevant"] == "true"
        out.append(f"- **relevant agreement:** {100 * g.agree_relevant.mean():.0f}% (n={len(g)})")
        out.append(f"- **trigger agreement:** {100 * g.loc[rel, 'agree_trigger'].mean():.0f}% "
                   f"(n={int(rel.sum())}, items I marked relevant)")
        out.append(f"- **action agreement:** {100 * g.loc[rel, 'agree_action'].mean():.0f}% "
                   f"(n={int(rel.sum())}, items I marked relevant)")
        out.append(f"\nWith n={int(rel.sum())}, one item moves trigger/action agreement by about "
                   f"{100 / max(int(rel.sum()), 1):.0f} points, so read these as directional.")
        hist = []
        for s in sorted(glob.glob(os.path.join(DATA_DIR, "golden_summary_v*.csv"))) + \
                [os.path.join(DATA_DIR, "golden_summary.csv")]:
            if os.path.exists(s):
                d = pd.read_csv(s)
                lab = os.path.basename(s)[len("golden_summary"):-4].strip("_") or "v3 (current)"
                row = {"prompt version": lab}
                row.update({r["field"]: f"{r['agreement_pct']}% (n={r['n']})" for _, r in d.iterrows()})
                hist.append(row)
        if len(hist) > 1:
            out.append("\n### Prompt iterations on the same golden set\n")
            out.append(md(pd.DataFrame(hist), index=False))
        if gset is not None and "notes" in gset:
            nmap = dict(zip(gset["id"].astype(str), gset["notes"]))
            g["notes"] = g["id"].astype(str).map(nmap)
        g["text"] = g["text"].map(one_line)
        cols = ["id", "source", "text", "human_relevant", "ai_relevant", "human_trigger",
                "ai_trigger", "human_action", "ai_action"]
        out.append("\n### All 20 items\n")
        out.append(md(g[cols], index=False))
        bad = g[~g.agree_relevant | (rel & ~(g.agree_trigger & g.agree_action))]
        out.append(f"\n\n### Where the engine disagreed with me ({len(bad)} items)\n")
        bcols = cols + (["notes"] if "notes" in g else [])
        if len(bad) and "notes" in bad:
            bad = bad.assign(notes=bad["notes"].fillna("").map(lambda x: one_line(x, 200)))
        out.append(md(bad[bcols], index=False) if len(bad) else "No disagreements.")

    out.append("\n\n## 3. Places where AI output was rejected or corrected\n")
    if corr is None or not len(corr):
        out.append("_Add 2-3 rows to data/corrections.csv (item_id, ai_output, corrected_to, why)._")
    else:
        for i, r in enumerate(corr.itertuples(), 1):
            out.append(f"**{i}. {one_line(r.item_id, 120)}**  \nAI said: {r.ai_output}  \n"
                       f"Corrected to: {r.corrected_to}  \nWhy: {r.why}\n")
    ind = load("industry_sip_2026.csv", os.path.join(BASE_DIR, "reference"))
    if ind is not None:
        out.append("\n\n## 4. Industry context used in the metric decomposition\n")
        out.append(md(ind.fillna(""), index=False))
        out.append("\nStoppage ratio = SIPs discontinued or matured ÷ new SIPs registered, industry-wide "
                   "(all investors, not only first-time). Monthly figures from AMFI as reported by the "
                   "linked news sources.")
    open(os.path.join(DATA_DIR, "Evidence_Log.md"), "w", encoding="utf-8").write("\n".join(out))
    print("Written data/Evidence_Log.md")

if __name__ == "__main__":
    main()
