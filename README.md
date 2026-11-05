# Groww SIP Continuation: Discovery Engine + MVP

| Part | What | Deploy to |
|---|---|---|
| `discovery-engine/` | Collects real reviews, Reddit, TradingQ&A, YouTube, social → LLM tags → themes, segments, opportunity ranking → golden-set check | Streamlit Community Cloud |
| `mvp/` | "SIP Check-in": eval-gated AI helper at the cancel-SIP / negative-return moment | Vercel |

Keys you need:
- **AI model (pick one):** Gemini API key, free tier, from aistudio.google.com (`LLM_PROVIDER=gemini`), or a paid Claude API key from platform.claude.com (`LLM_PROVIDER=anthropic`).
- **YouTube Data API key** (free).
- Reddit: new API keys are no longer issued (Nov 2025). Collect Reddit posts by hand into `data/social_manual.csv`.

On the free Gemini tier, tagging sends 15 items per request and waits between requests. If the daily free limit runs out, `tag.py` stops with errors; run it again the next day and it continues where it stopped. To finish in one day, sample: `python tag.py --max-per-source 3000`.

---
## A. Discovery engine: run on your machine

```bash
cd discovery-engine
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                     # paste your keys
mkdir data
# copy your Play Store export into data/  (file name: groww_reviews_last5y.csv)
```

| Step | Command | Output |
|---|---|---|
| 1. Collect | `python collect.py` | `data/raw.csv`, `data/filtered.csv`, `data/volume.csv` |
| 2. Test tagging | `python tag.py --limit 50` then open `data/tagged.csv` and read 10 rows | |
| 3. Tag all | `python tag.py` (safe to stop and re-run; it resumes) | `data/tagged.csv` |
| 4. Analyse | `python aggregate.py` | opportunities, segments, expectations, `synthesis.md` |
| 5. Golden set | `python make_golden.py` → open `golden_set.csv`, label the 3 `human_*` columns yourself | `golden_set.csv` (20 real items) |
| 6. Check AI vs you | `python golden_eval.py` | `data/golden_results.csv`, `golden_summary.csv` |
| 7. Corrections | write 2-3 rows in `data/corrections.csv`: `item_id,ai_output,corrected_to,why` | |
| 8. Evidence Log | `python evidence_log.py` → paste `data/Evidence_Log.md` into a Google Doc, "Anyone with the link can view" | |
| 9. MVP eval set | `python make_mvp_golden.py` → check each intent in `../mvp/evals/golden.json`, set `review_needed` to false | |
| 10. Dashboard | `streamlit run app.py` | |

Run only some sources: `python collect.py reddit youtube`.
Too many items to tag? `python tag.py --max-per-source 4000` takes a random sample of each source.

**Getting the keys**
- YouTube: console.cloud.google.com → new project → enable "YouTube Data API v3" → Credentials → API key.
  Leave `YOUTUBE_VIDEO_IDS` empty and the engine searches for SIP videos itself.
- Social: copy real posts (X, Instagram, LinkedIn, Facebook groups) into `data/social_manual.csv`
  with columns `source,id,date,url,text`. Keep the URL so every item is traceable.

**Deploy the dashboard:** push to GitHub (the `.gitignore` leaves out the 46 MB export) →
share.streamlit.io → main file `discovery-engine/app.py` → Secrets: `LLM_PROVIDER = "gemini"` and `GEMINI_API_KEY = "AIza..."`.

## B. MVP (Vercel)

```bash
npm i -g vercel
cd mvp
vercel login
vercel env add LLM_PROVIDER      # type: gemini
vercel env add GEMINI_API_KEY
vercel dev            # http://localhost:3000
vercel --prod         # this URL is your "Deployed MVP" link
```

Eval (after step 9 above):
```bash
BASE_URL=https://your-app.vercel.app GEMINI_API_KEY=AIza... node evals/run_eval.mjs
```
Reports intent accuracy, fallback rate, and an **independent judge** with a different rubric from the in-app checker
(on Gemini, set `GEMINI_JUDGE_MODEL` to a different model than `GEMINI_MODEL` if your free tier allows it). Then open `evals/results.csv`, fill `human_safe` and `human_helpful` yourself, and report both.

## How the eval gate works
1. Companion drafts a JSON answer (intent, reply, neutral options).
2. `lib/guard.js`: sentence-level rules. Fund/AMC names and urgency words are always blocked. Advice,
   predictions and "you should" are blocked unless the sentence is a refusal or reported speech.
3. LLM checker reviews the draft against the compliance rules.
4. Any failure or error → safe fallback (generic options + AMFI/SEBI links). The UI shows whether the check passed.

## Industry context
`discovery-engine/reference/industry_sip_2026.csv`: AMFI SIP registrations, discontinued/matured SIPs and
stoppage ratio for Jan–Sep 2026, with the news source for each month. Verify against AMFI's own monthly release
before using in the deck.
