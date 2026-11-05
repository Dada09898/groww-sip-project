"""Step 4+5: count themes, compare segments, score opportunities, cluster start-expectations,
and write an LLM synthesis.
Outputs in data/: theme_counts.csv, opportunities.csv, opportunity_quotes.csv,
segment_*.csv, lifecycle_x_trigger.csv, continuers_vs_dropoffs.csv, expectations.csv, synthesis.md"""
import json, re
import pandas as pd
from config import DATA_DIR
from llm import complete

# trigger -> (opportunity area, fixability 1-5 under the project rules: no fund advice, no fear/FOMO)
# Fixability is YOUR judgement. State it as an assumption in the deck.
OPPORTUNITY_MAP = {
    "returns_negative": ("A. Can't judge if SIP is 'working'", 5),
    "returns_unclear":  ("A. Can't judge if SIP is 'working'", 5),
    "cash_crunch":      ("B. Temporary cash crunch -> cancel instead of skip", 5),
    "job_loss":         ("B. Temporary cash crunch -> cancel instead of skip", 5),
    "mandate_or_payment_failure": ("C. Autopay/mandate failure -> silent lapse", 4),
    "app_confusion":    ("C2. Confusing SIP controls (stop/pause/skip/redeem)", 4),
    "app_bug":          ("C3. App errors block SIP set-up or instalments", 2),
    "support_service":  ("H. Support/refund failures erode trust", 3),
    "trust_safety":     ("E. Trust / is my money invested?", 3),
    "goal_changed":     ("F. Lost the reason to invest", 4),
    "external_advice":  ("G. Swayed by outside advice", 2),
    "fund_doubt":       ("D. Doubt about chosen fund (blocked: no fund advice)", 1),
}
SEVERITY = {"stopped": 5, "considering_stop": 4, "blocked": 4, "paused": 3, "skipped": 3, "reduced": 3}
FIELDS = ["trigger", "action", "lifecycle_stage", "what_they_check", "outside_help", "income",
          "income_stability", "age_band", "money_source", "influenced_by", "emotion"]

def _ask_json(prompt, max_tokens=4000):
    txt = re.sub(r"```json|```", "", complete(prompt, max_tokens=max_tokens, kind="synth", json_mode=True))
    return json.loads(re.search(r"[\[{].*[\]}]", txt, re.S).group(0))

def cluster_expectations(rel):
    """Free-text 'expectation_at_start' -> 6-10 themes with counts."""
    s = rel["expectation_at_start"].dropna().astype(str).str.strip()
    s = s[~s.str.lower().isin(["unknown", "", "none", "nan"])]
    if len(s) < 10:
        print("Expectations: fewer than 10 stated, skipping clustering")
        return None
    phrases = s.value_counts()
    sample = list(phrases.index[:150])
    cats = _ask_json("These are phrases describing what first-time SIP investors expected when they "
                     "started. Propose 6 to 10 mutually exclusive themes (short names). Return JSON "
                     f"list of strings only.\n\n{sample}", 800)
    mapping = {}
    uniq = list(phrases.index)
    for i in range(0, len(uniq), 60):
        chunk = uniq[i:i + 60]
        part = _ask_json(f"Themes: {cats + ['other']}\nAssign each phrase to exactly one theme. "
                         "Return a JSON object {phrase: theme} only.\n\n" + json.dumps(chunk))
        mapping.update(part)
    rel = rel.copy()
    rel["expectation_theme"] = rel["expectation_at_start"].map(mapping)
    out = (rel.dropna(subset=["expectation_theme"])
              .groupby("expectation_theme")
              .agg(mentions=("id", "count"),
                   example=("expectation_at_start", "first"))
              .sort_values("mentions", ascending=False))
    out.to_csv(f"{DATA_DIR}/expectations.csv")
    return out

def main():
    df = pd.read_csv(f"{DATA_DIR}/tagged.csv", low_memory=False)
    rel = df[df["relevant"].astype(str).str.lower() == "true"].copy()
    print(f"Relevant: {len(rel):,} of {len(df):,}")
    for c in FIELDS + ["quote", "confidence", "expectation_at_start", "url"]:
        if c not in rel:
            rel[c] = "unknown" if c in FIELDS else None

    counts = {c: rel[c].fillna("unknown").value_counts() for c in FIELDS}
    pd.concat(counts, names=["field", "value"]).rename("n").to_csv(f"{DATA_DIR}/theme_counts.csv")

    # Opportunity scoring: share of mentions x how severe the action is x fixability.
    # trigger "none" = no problem (happy starters/continuers), so it is not an opportunity.
    rel["opportunity"] = rel["trigger"].map(lambda t: OPPORTUNITY_MAP.get(t, ("Other", 1))[0])
    rel["fixability"] = rel["trigger"].map(lambda t: OPPORTUNITY_MAP.get(t, ("Other", 1))[1])
    rel["severity"] = rel["action"].map(SEVERITY).fillna(2)
    rel["year"] = pd.to_datetime(rel["date"], errors="coerce", utc=True, format="mixed").dt.year
    prob = rel[rel["trigger"] != "none"]

    def score(x):
        o = x.groupby("opportunity").agg(mentions=("id", "count"),
                                         avg_severity=("severity", "mean"),
                                         fixability=("fixability", "first"),
                                         n_sources=("source", "nunique"))
        o["share_pct"] = (100 * o["mentions"] / o["mentions"].sum()).round(1)
        o["avg_severity"] = o["avg_severity"].round(2)
        o["score"] = (o["share_pct"] * o["avg_severity"] * o["fixability"] / 25).round(1)
        return o.sort_values("score", ascending=False)

    opp = score(prob)
    opp.to_csv(f"{DATA_DIR}/opportunities.csv")
    print(f"Problem items (trigger != none): {len(prob):,}")
    print(opp.to_string())
    # Same ranking in three cuts that correct for source and time bias
    score(prob[prob["year"] >= 2025]).to_csv(f"{DATA_DIR}/opportunities_2025_26.csv")
    score(prob[prob["source"] != "play_store"]).to_csv(f"{DATA_DIR}/opportunities_non_playstore.csv")
    score(prob[prob["action"].isin(["stopped", "considering_stop", "reduced", "paused"])]) \
        .to_csv(f"{DATA_DIR}/opportunities_voluntary_drop.csv")
    pd.crosstab(prob["opportunity"], prob["year"]).to_csv(f"{DATA_DIR}/opportunity_x_year.csv")

    # Where each opportunity shows up (reviews vs Reddit vs YouTube tell different stories)
    pd.crosstab(prob["opportunity"], prob["source"]).to_csv(f"{DATA_DIR}/opportunity_x_source.csv")

    # Traceable evidence: top 5 quotes per opportunity with source, id, url
    rel["confidence"] = pd.to_numeric(rel["confidence"], errors="coerce")
    q = (prob.sort_values("confidence", ascending=False).groupby("opportunity").head(5)
            [["opportunity", "source", "id", "date", "url", "quote", "text"]])
    q.to_csv(f"{DATA_DIR}/opportunity_quotes.csv", index=False)

    # Behaviour over time after starting
    pd.crosstab(rel["lifecycle_stage"], rel["trigger"]).to_csv(f"{DATA_DIR}/lifecycle_x_trigger.csv")

    # Segment comparisons
    seg = pd.crosstab(rel["income"], rel["trigger"], normalize="index").round(2)
    seg.to_csv(f"{DATA_DIR}/segment_x_trigger.csv")
    for dim in ["income_stability", "age_band", "money_source", "influenced_by"]:
        known = rel[rel[dim] != "unknown"]
        if len(known):
            t = pd.crosstab(known[dim], known["action"], normalize="index").round(2)
            t["n"] = known[dim].value_counts()
            t.to_csv(f"{DATA_DIR}/segment_{dim}_x_action.csv")

    # Continuers vs drop-offs
    rel["group"] = rel["action"].map(lambda x: "continued" if x == "continuing" else
                                     ("dropped" if x in ["stopped", "paused", "considering_stop"] else "other"))
    comp = rel[rel.group != "other"]
    if comp["group"].nunique() == 2:
        pd.concat({c: pd.crosstab(comp[c], comp["group"], normalize="columns").round(2)
                   for c in ["what_they_check", "outside_help", "trigger", "influenced_by"]}) \
          .to_csv(f"{DATA_DIR}/continuers_vs_dropoffs.csv")
    else:
        print("Not enough continuers AND drop-offs to compare")

    print("\nAll tables saved. Now asking the LLM for expectation themes and the synthesis...")
    try:
        exp = cluster_expectations(rel)
    except Exception as e:
        print(f"Expectation clustering failed ({e}). Tables are fine; re-run later.")
        exp = None

    quotes = q.groupby("opportunity")["quote"].apply(lambda s: list(s.dropna())).to_dict()
    unknown_share = {c: round(100 * (rel[c] == "unknown").mean()) for c in
                     ["age_band", "income_stability", "money_source", "influenced_by", "lifecycle_stage"]}
    prompt = (f"Opportunity table:\n{opp.to_string()}\n\nOpportunity x source:\n"
              f"{pd.crosstab(rel['opportunity'], rel['source']).to_string()}\n\n"
              f"Lifecycle x trigger:\n{pd.crosstab(rel['lifecycle_stage'], rel['trigger']).to_string()}\n\n"
              f"Segment x trigger:\n{seg.to_string()}\n\n"
              f"Start expectations:\n{exp.to_string() if exp is not None else 'not enough data'}\n\n"
              f"Percent of items where segment field is unknown: {unknown_share}\n\n"
              f"Sample quotes:\n{quotes}\n\n"
              "Write a synthesis for a PM whose goal is 12-month SIP continuation of first-time "
              "investors on Groww. Answer each: why people start and what they expect; what changes "
              "in the months after; what leads to pause/reduce/stop; what they check and how often; "
              "what confuses or worries them in the app; what they do outside the app; what separates "
              "continuers from drop-offs; how segments differ; unmet needs. Cite counts for every "
              "claim. Flag where evidence is weak (small n, or segment field mostly unknown) and note "
              "that app-store reviews over-represent technical complaints. Do not recommend funds. "
              "Use markdown headings.")
    try:
        text = complete(prompt, max_tokens=3000, kind="synth")
        open(f"{DATA_DIR}/synthesis.md", "w", encoding="utf-8").write(text)
        print("Synthesis -> data/synthesis.md")
    except Exception as e:
        print(f"Synthesis failed ({e}). Re-run: python aggregate.py")

if __name__ == "__main__":
    main()
