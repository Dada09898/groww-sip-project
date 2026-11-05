# Final check 2026-11-05 01:10

```
== 1. Sources and volume ==
OK      volume.csv: app_store=49, play_store=210,327, tradingqna=799, youtube=1,379
WARN    No Reddit items in volume.csv
        -> PDF lists this source. Add it, or say clearly in the Evidence Log why it is missing.
WARN    No other social-media source (X / Instagram / LinkedIn / Facebook)
        -> Add a few real posts with URLs to data/social_manual.csv, or state the gap in the Evidence Log.

== 2. Re-tag with the v3 prompt ==
OK      tagged.csv: 3,850 rows, 1,024 relevant
OK      tags contain v3 values (app_bug / blocked), so this is the new tagging
OK      tagging progress: 3,850 of 3,850 sampled items (100%)
OK      tagged_v2.csv backup exists (old tags kept for before/after)

== 3. Analysis (aggregate.py) on the new tags ==
OK      data/opportunities.csv
OK      data/opportunity_x_source.csv
OK      data/opportunity_quotes.csv
OK      data/lifecycle_x_trigger.csv
OK      data/segment_x_trigger.csv
OK      data/continuers_vs_dropoffs.csv
OK      data/expectations.csv
OK      data/theme_counts.csv
OK      data/synthesis.md

== 4. Golden set and prompt versions ==
OK      golden_set.csv: 20 items, 0 unlabelled
OK      3 prompt versions found for the before/after table
        (table written to data/prompt_history.md: paste it into the Evidence Log)

== 5. Corrections and Evidence Log ==
OK      corrections.csv: 3 rows
OK      Evidence_Log.md is up to date

== 6. MVP eval set and results ==
WARN    mvp/evals/golden.json: 0 real + 5 red-team, 0 still review_needed
        -> Run make_mvp_golden.py ONCE, review intents, set review_needed=false
MISSING mvp/evals/results.csv
        -> BASE_URL=<your vercel url> node evals/run_eval.mjs

== 7. Not checkable by code: tick these yourself ==
[ ]     Streamlit link opens in an incognito window and shows the NEW numbers (push data/ to GitHub again)
[ ]     Vercel MVP link opens in an incognito window, disclaimer visible, quality-check badge visible
[ ]     Evidence Log Google Doc: 'Anyone with the link can view', updated after the re-tag
[ ]     Deck: 10 slides max, file name NL_Groww.pdf, under 40 MB, your name nowhere
[ ]     Deck: every font 14 or larger, slide titles state the message, colour-blind-safe colours
[ ]     Deck: numbers on slides match the NEW opportunities.csv / golden summary
[ ]     Deck: 5-6 interviews + at least 3 MVP user tests, with what you would change next
[ ]     Deck: 'where AI earns its place / what a non-AI version would miss' is written
```

4 item(s) need attention.
