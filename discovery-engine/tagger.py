"""LLM tagging with a fixed schema. Used by tag.py (batch), golden_eval.py and the Streamlit app."""
import json, re
from llm import complete

SCHEMA_PROMPT = """You are a research analyst. Classify user text about mutual fund SIPs
(it may be English, Hindi or Hinglish). For each text, produce a JSON object like this (no markdown):
{
 "relevant": true or false,
 "lifecycle_stage": "starting|month_1_3|month_4_12|after_12|unknown",
 "action": "started|continuing|considering_stop|paused|reduced|skipped|stopped|blocked|unknown",
 "trigger": "returns_negative|returns_unclear|cash_crunch|job_loss|mandate_or_payment_failure|app_bug|app_confusion|fund_doubt|external_advice|goal_changed|trust_safety|support_service|other|none",
 "what_they_check": "returns_pct|portfolio_value|nav|nothing|unknown",
 "outside_help": "reddit|youtube|friend_family|advisor|customer_support|none|unknown",
 "income": "salaried|variable|student|unknown",
 "income_stability": "stable|unstable|unknown",
 "age_band": "under_25|25_34|35_plus|unknown",
 "money_source": "salary|savings|bonus_windfall|family_money|unknown",
 "influenced_by": "self|friend_family|youtube_finfluencer|reddit_community|employer|app_ad|unknown",
 "expectation_at_start": "short phrase of what they expected when starting, or unknown",
 "emotion": "anxious|confused|regret|calm|angry|neutral",
 "quote": "shortest exact phrase from the text that proves the tags",
 "confidence": number between 0 and 1
}
RELEVANT = true only if the text describes the writer's OWN experience of starting, continuing, pausing,
skipping, reducing or stopping a SIP / mutual fund investment, or a problem that blocked one of their
SIP instalments or SIP set-up (mandate, autopay, payment, app error). Set relevant=false for: generic praise
("best app for SIP"), feature requests, IPO, stocks, F&O, loans, gold, and questions with no personal experience.

ACTION = what the writer did or clearly says they intend, based on their own words. Do not invent.
- started: says they started or began SIP / mutual fund investing.
- continuing: says their SIP is still running, or that they increased the SIP amount.
- considering_stop: says they are thinking of stopping, want to leave the app, are switching to
  another platform, or ask how to stop / cancel their SIP.
- stopped: says they cancelled, stopped, sold or withdrew. If they cancelled after a payment
  problem, use stopped (not blocked).
- skipped / paused / reduced: says they did it.
- blocked: tried to start or continue but an app error, payment or mandate problem prevented it,
  and they do NOT say they stopped or are leaving.
- unknown: none of the above is said.

TRIGGER = the main reason behind the action or complaint.
- app_bug: crashes, errors, orders not placed, wrong numbers shown.
- app_confusion: they don't understand SIP controls or terms (stop vs pause vs skip vs redeem, XIRR).
- mandate_or_payment_failure: autopay/mandate/bank debit problems for a SIP.
- support_service: the main complaint is customer support or refunds.

If relevant=false, set trigger="none" and action="unknown".
Use "unknown" when the text does not say. Never invent age, income, stage or source of money."""

def _parse(raw):
    raw = re.sub(r"```json|```", "", raw).strip()
    m = re.search(r"[\[{].*[\]}]", raw, re.S)
    return json.loads(m.group(0))

def _clean(o):
    """Make irrelevant items consistent, whatever the model returned."""
    if str(o.get("relevant")).lower() != "true":
        o["relevant"] = False
        o["trigger"], o["action"] = "none", "unknown"
    return o

def tag_text(text, attempts=3):
    """Tag ONE text. Returns the tag dict, or {"error": "..."} so callers can retry later."""
    last = ""
    for _ in range(attempts):
        try:
            out = _parse(complete(f"TEXT:\n{str(text)[:3000]}", system=SCHEMA_PROMPT,
                                  max_tokens=450, kind="tag", json_mode=True))
            if isinstance(out, list):
                out = out[0]
            return _clean(out)
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
    return {"error": last[:300]}

def tag_batch(texts, attempts=2):
    """Tag several texts in ONE call (saves requests on the free tier).
    Returns a list of dicts in the same order; failed items get {"error": ...}."""
    if len(texts) == 1:
        return [tag_text(texts[0])]
    items = "\n\n".join(f"### ITEM {i}\n{str(t)[:1500]}" for i, t in enumerate(texts))
    prompt = (f"Classify each of the {len(texts)} items below separately. Return ONLY a JSON array "
              f"with exactly {len(texts)} objects in the same order, each with an extra field "
              f"\"item\" = the item number.\n\n{items}")
    last = ""
    for _ in range(attempts):
        try:
            out = _parse(complete(prompt, system=SCHEMA_PROMPT, max_tokens=320 * len(texts),
                                  kind="tag", json_mode=True))
            if isinstance(out, dict):
                out = out.get("items") or out.get("results") or [out]
            by_idx = {int(o.get("item", i)): o for i, o in enumerate(out) if isinstance(o, dict)}
            res = []
            for i in range(len(texts)):
                o = by_idx.get(i)
                if o is None:
                    res.append({"error": "missing_in_batch"})
                else:
                    o.pop("item", None)
                    res.append(_clean(o))
            return res
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
    return [{"error": last[:300]} for _ in texts]
