"""Final check before submission. READ-ONLY: it changes none of your existing files.
It only writes two new files: data/final_check.md and data/prompt_history.md

Put this file in discovery-engine/ and run:
    python check_final.py
"""
import os, glob, json
from datetime import datetime
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
MVP = os.path.join(BASE, "..", "mvp")
lines, problems = [], []

def p(path):
    return os.path.join(DATA, path)

def mtime(path):
    return os.path.getmtime(path) if os.path.exists(path) else 0

def ok(msg, fix=""):
    lines.append(f"OK      {msg}")

def warn(msg, fix=""):
    lines.append(f"WARN    {msg}" + (f"\n        -> {fix}" if fix else ""))
    problems.append(msg)

def miss(msg, fix=""):
    lines.append(f"MISSING {msg}" + (f"\n        -> {fix}" if fix else ""))
    problems.append(msg)

def read(path):
    try:
        return pd.read_csv(path, low_memory=False)
    except Exception:
        return None

lines.append("== 1. Sources and volume ==")
vol = read(p("volume.csv"))
if vol is None:
    miss("data/volume.csv", "python collect.py")
else:
    vol = vol.set_index(vol.columns[0])
    srcs = [s for s in vol.index if s != "TOTAL"]
    ok(f"volume.csv: {', '.join(f'{s}={int(vol.loc[s].iloc[0]):,}' for s in srcs)}")
    need = {"Play Store": lambda s: s == "play_store", "App Store": lambda s: s == "app_store",
            "Reddit": lambda s: "reddit" in s, "TradingQ&A": lambda s: "tradingqna" in s,
            "YouTube": lambda s: s == "youtube"}
    for name, test in need.items():
        if not any(test(s) for s in srcs):
            warn(f"No {name} items in volume.csv",
                 "PDF lists this source. Add it, or say clearly in the Evidence Log why it is missing.")
    other = [s for s in srcs if not any(t(s) for t in need.values())]
    if not other:
        warn("No other social-media source (X / Instagram / LinkedIn / Facebook)",
             "Add a few real posts with URLs to data/social_manual.csv, or state the gap in the Evidence Log.")

lines.append("\n== 2. Re-tag with the v3 prompt ==")
tagged_path = p("tagged.csv")
tag = read(tagged_path)
if tag is None:
    miss("data/tagged.csv", "python tag.py --max-per-source 3000")
else:
    rel = tag[tag["relevant"].astype(str).str.lower() == "true"]
    ok(f"tagged.csv: {len(tag):,} rows, {len(rel):,} relevant")
    acts = set(tag.get("action", pd.Series(dtype=str)).astype(str).str.lower())
    trigs = set(tag.get("trigger", pd.Series(dtype=str)).astype(str).str.lower())
    if "blocked" in acts or "app_bug" in trigs:
        ok("tags contain v3 values (app_bug / blocked), so this is the new tagging")
    else:
        warn("tagged.csv has no 'app_bug' or 'blocked' values: it still looks like OLD tags",
             "Rename-Item data\\tagged.csv tagged_v2.csv ; python tag.py --max-per-source 3000")
    filt = read(p("filtered.csv"))
    if filt is not None:
        expected = int(filt.groupby("source").size().clip(upper=3000).sum())
        done = tag["id"].astype(str).nunique()
        pct = 100 * done / max(expected, 1)
        (ok if pct >= 98 else warn)(
            f"tagging progress: {done:,} of {expected:,} sampled items ({pct:.0f}%)",
            "" if pct >= 98 else "Quota ran out. Run the same tag.py command again; it resumes.")
    errs = read(p("tag_errors.csv"))
    if errs is not None and len(errs):
        warn(f"{len(errs)} items failed in the last tag run", "Run tag.py again to retry them.")
    if os.path.exists(p("tagged_v2.csv")):
        ok("tagged_v2.csv backup exists (old tags kept for before/after)")

lines.append("\n== 3. Analysis (aggregate.py) on the new tags ==")
agg_src = open(os.path.join(BASE, "aggregate.py"), encoding="utf-8").read()
if '"app_bug"' not in agg_src:
    warn("aggregate.py does not mention 'app_bug': app errors will fall into 'Other' with fixability 1",
         "Send me your aggregate.py and I will add the mapping.")
if '"blocked"' not in agg_src:
    warn("aggregate.py does not mention 'blocked': blocked users get the default severity 2",
         "Send me your aggregate.py and I will add it.")
for f in ["opportunities.csv", "opportunity_x_source.csv", "opportunity_quotes.csv",
          "lifecycle_x_trigger.csv", "segment_x_trigger.csv", "continuers_vs_dropoffs.csv",
          "expectations.csv", "theme_counts.csv", "synthesis.md"]:
    path = p(f)
    if not os.path.exists(path):
        miss(f"data/{f}", "python -u aggregate.py")
    elif mtime(path) < mtime(tagged_path):
        warn(f"data/{f} is OLDER than tagged.csv (built from old tags)", "python -u aggregate.py")
    else:
        ok(f"data/{f}")
opp = read(p("opportunities.csv"))
if opp is not None:
    opp = opp.set_index(opp.columns[0])
    if "Other" in opp.index and "share_pct" in opp and opp.loc["Other", "share_pct"] > 25:
        warn(f"'Other' is {opp.loc['Other', 'share_pct']}% of relevant mentions",
             "Too big to ignore. Check which triggers end up there (likely app_bug / none).")

lines.append("\n== 4. Golden set and prompt versions ==")
gs = read(os.path.join(BASE, "golden_set.csv"))
if gs is None:
    miss("golden_set.csv")
else:
    unl = gs["human_relevant"].isna().sum() if "human_relevant" in gs else len(gs)
    (ok if len(gs) >= 18 and unl == 0 else warn)(f"golden_set.csv: {len(gs)} items, {unl} unlabelled")
summaries = sorted(glob.glob(p("golden_summary_v*.csv"))) + (
    [p("golden_summary.csv")] if os.path.exists(p("golden_summary.csv")) else [])
hist = []
for s in summaries:
    d = read(s)
    if d is None:
        continue
    label = os.path.basename(s).replace("golden_summary", "").replace(".csv", "").strip("_") or "latest (v3)"
    row = {"prompt version": label}
    for _, r in d.iterrows():
        row[r["field"]] = f"{r['agreement_pct']}% (n={r['n']})"
    hist.append(row)
if len(hist) >= 2:
    ok(f"{len(hist)} prompt versions found for the before/after table")
elif hist:
    warn("Only one golden_summary file: the Evidence Log can't show the v2 -> v3 improvement",
         "Keep golden_summary_v2.csv in data/ (you renamed it earlier).")
else:
    miss("data/golden_summary.csv", "python golden_eval.py")
if hist:
    h = pd.DataFrame(hist)
    note = ("\n\nRelevance is scored on all golden items; trigger and action only on the items the "
            "human marked relevant, so each action/trigger item moves the score by about 12 points (n=8).\n")
    open(p("prompt_history.md"), "w", encoding="utf-8").write(
        "## Prompt iterations on the same golden set\n\n" + h.to_markdown(index=False) + note)
    lines.append("        (table written to data/prompt_history.md: paste it into the Evidence Log)")

lines.append("\n== 5. Corrections and Evidence Log ==")
corr = read(p("corrections.csv"))
if corr is None:
    miss("data/corrections.csv")
else:
    cols_ok = {"item_id", "ai_output", "corrected_to", "why"} <= set(corr.columns)
    (ok if len(corr) >= 2 and cols_ok else warn)(
        f"corrections.csv: {len(corr)} rows" + ("" if cols_ok else " (wrong column names)"),
        "" if len(corr) >= 2 and cols_ok else "Need 2-3 rows: item_id,ai_output,corrected_to,why")
ev = p("Evidence_Log.md")
if not os.path.exists(ev):
    miss("data/Evidence_Log.md", "python evidence_log.py")
else:
    txt = open(ev, encoding="utf-8").read()
    newest = max(mtime(tagged_path), mtime(p("corrections.csv")), mtime(p("golden_summary.csv")))
    if mtime(ev) < newest:
        warn("Evidence_Log.md is older than tagged.csv / corrections.csv / golden results",
             "python evidence_log.py   (then paste it into the Google Doc again)")
    elif "_not generated yet_" in txt or "Add 2-3 rows" in txt:
        warn("Evidence_Log.md still has empty sections", "Fill the missing file, then python evidence_log.py")
    else:
        ok("Evidence_Log.md is up to date")

lines.append("\n== 6. MVP eval set and results ==")
gj = os.path.join(MVP, "evals", "golden.json")
if os.path.exists(gj):
    items = json.load(open(gj, encoding="utf-8"))
    real = [i for i in items if i.get("source") != "red_team"]
    todo = [i for i in items if i.get("review_needed")]
    (ok if len(real) >= 15 and not todo else warn)(
        f"mvp/evals/golden.json: {len(real)} real + {len(items) - len(real)} red-team, "
        f"{len(todo)} still review_needed",
        "" if len(real) >= 15 and not todo else "Run make_mvp_golden.py ONCE, review intents, set review_needed=false")
else:
    miss("mvp/evals/golden.json")
res = os.path.join(MVP, "evals", "results.csv")
r = read(res)
if r is None:
    miss("mvp/evals/results.csv", "BASE_URL=<your vercel url> node evals/run_eval.mjs")
else:
    filled = all(c in r and r[c].notna().all() for c in ["human_safe", "human_helpful"])
    (ok if filled else warn)(f"mvp/evals/results.csv: {len(r)} rows, human columns "
                             + ("filled" if filled else "NOT filled"),
                             "" if filled else "Fill human_safe and human_helpful yourself")

lines.append("\n== 7. Not checkable by code: tick these yourself ==")
for t in ["Streamlit link opens in an incognito window and shows the NEW numbers (push data/ to GitHub again)",
          "Vercel MVP link opens in an incognito window, disclaimer visible, quality-check badge visible",
          "Evidence Log Google Doc: 'Anyone with the link can view', updated after the re-tag",
          "Deck: 10 slides max, file name NL_Groww.pdf, under 40 MB, your name nowhere",
          "Deck: every font 14 or larger, slide titles state the message, colour-blind-safe colours",
          "Deck: numbers on slides match the NEW opportunities.csv / golden summary",
          "Deck: 5-6 interviews + at least 3 MVP user tests, with what you would change next",
          "Deck: 'where AI earns its place / what a non-AI version would miss' is written"]:
    lines.append(f"[ ]     {t}")

report = (f"# Final check {datetime.now():%Y-%m-%d %H:%M}\n\n```\n" + "\n".join(lines) + "\n```\n"
          + f"\n{len(problems)} item(s) need attention.\n")
open(p("final_check.md"), "w", encoding="utf-8").write(report)
print("\n".join(lines))
print(f"\n{len(problems)} item(s) need attention. Saved to data/final_check.md")
