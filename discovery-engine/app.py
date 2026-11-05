"""Streamlit front-end = the testable link for the Discovery Engine.
Deploy on Streamlit Community Cloud (main file: discovery-engine/app.py)."""
import os
import pandas as pd, plotly.express as px, streamlit as st

try:   # st.secrets raises when no secrets.toml exists (local runs use .env instead)
    for k in ["ANTHROPIC_API_KEY", "GEMINI_API_KEY", "LLM_PROVIDER", "GEMINI_TAG_MODEL"]:
        if k in st.secrets:
            os.environ[k] = str(st.secrets[k])
except Exception:
    pass
from tagger import tag_text
from config import DATA_DIR, BASE_DIR

st.set_page_config(page_title="SIP Continuation Discovery Engine", layout="wide")
st.title("SIP continuation discovery engine: Groww")
st.caption("Collects Play Store, App Store, Reddit, TradingQ&A and YouTube comments → keyword filter "
           "→ LLM tags each item with a fixed schema → theme counts, segment comparisons, opportunity "
           "ranking → checked against a hand-labelled golden set of real items.")

def load(name, base=DATA_DIR):
    p = os.path.join(base, name)
    return pd.read_csv(p, low_memory=False) if os.path.exists(p) else None

tabs = st.tabs(["Try the tagger", "Sources", "Findings", "Opportunities", "Segments", "Golden set"])

with tabs[0]:
    st.subheader("Paste any review or comment")
    txt = st.text_area("Text", "Salary late this month, cancelled my SIP. Will restart later maybe.", height=120)
    if st.button("Tag this text"):
        with st.spinner("Tagging"):
            st.json(tag_text(txt))

with tabs[1]:
    vol = load("volume.csv")
    st.dataframe(vol) if vol is not None else st.info("Run collect.py")
    ind = load("industry_sip_2026.csv", os.path.join(BASE_DIR, "reference"))
    if ind is not None:
        st.subheader("Industry context: AMFI SIP stoppage ratio, 2026")
        st.plotly_chart(px.line(ind, x="month", y="stoppage_ratio_pct", markers=True),
                        use_container_width=True)
        st.caption("Discontinued or matured SIPs ÷ new SIPs registered. Industry-wide, not first-time investors only.")

with tabs[2]:
    df = load("tagged.csv")
    if df is None:
        st.info("No data/tagged.csv yet. Run the pipeline locally and commit the data folder.")
    else:
        rel = df[df["relevant"].astype(str).str.lower() == "true"]
        c1, c2, c3 = st.columns(3)
        c1.metric("Items tagged", f"{len(df):,}"); c2.metric("SIP-relevant", f"{len(rel):,}")
        c3.metric("Sources", df["source"].nunique())
        field = st.selectbox("Break down by", ["trigger", "action", "lifecycle_stage",
                                               "what_they_check", "outside_help", "income",
                                               "income_stability", "age_band", "money_source",
                                               "influenced_by", "emotion"])
        vc = rel[field].value_counts().reset_index(); vc.columns = [field, "count"]
        st.plotly_chart(px.bar(vc, x="count", y=field, orientation="h"), use_container_width=True)
        src = st.multiselect("Filter source", sorted(rel["source"].unique()))
        view = rel[rel["source"].isin(src)] if src else rel
        cols = [c for c in ["source", "date", "trigger", "action", "lifecycle_stage", "quote", "text", "url"]
                if c in view]
        st.dataframe(view[cols].head(300))
    exp = load("expectations.csv")
    if exp is not None:
        st.subheader("What people expected when they started"); st.dataframe(exp)
    syn = os.path.join(DATA_DIR, "synthesis.md")
    if os.path.exists(syn):
        st.markdown(open(syn, encoding="utf-8").read())

with tabs[3]:
    opp = load("opportunities.csv")
    if opp is None:
        st.info("Run aggregate.py to generate opportunities.csv")
    else:
        st.caption("score = share of mentions × average severity of the action × fixability (1-5, analyst judgement) ÷ 25")
        st.dataframe(opp)
        st.plotly_chart(px.scatter(opp, x="share_pct", y="fixability", size="mentions",
                                   text="opportunity", title="Frequency vs fixability"),
                        use_container_width=True)
        for n, title in [("opportunities_2025_26.csv", "Ranking with 2025-26 items only (recent problems)"),
                         ("opportunities_non_playstore.csv", "Ranking without Play Store (removes app-review bias)"),
                         ("opportunities_voluntary_drop.csv", "Ranking among people who stopped / reduced / paused"),
                         ("opportunity_x_year.csv", "Mentions per year"),
                         ("opportunity_x_source.csv", "Where each opportunity shows up"),
                         ("opportunity_quotes.csv", "Evidence quotes")]:
            t = load(n)
            if t is not None:
                st.subheader(title); st.dataframe(t)

with tabs[4]:
    for n, title in [("lifecycle_x_trigger.csv", "Lifecycle stage × trigger"),
                     ("segment_x_trigger.csv", "Income type × trigger"),
                     ("continuers_vs_dropoffs.csv", "What separates continuers from drop-offs")]:
        t = load(n)
        if t is not None:
            st.subheader(title); st.dataframe(t)
    for dim in ["income_stability", "age_band", "money_source", "influenced_by"]:
        t = load(f"segment_{dim}_x_action.csv")
        if t is not None:
            st.subheader(f"{dim} × action"); st.dataframe(t)

with tabs[5]:
    gs, gr = load("golden_summary.csv"), load("golden_results.csv")
    if gs is None:
        st.info("Label golden_set.csv, then run golden_eval.py.")
    else:
        cols = st.columns(len(gs))
        for c, (_, r) in zip(cols, gs.iterrows()):
            c.metric(f"{r['field']} agreement", f"{r['agreement_pct']}%", help=f"n={r['n']}")
        st.dataframe(gr)
