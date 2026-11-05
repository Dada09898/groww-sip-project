"""Step 3: tag filtered items with the LLM.
Saves every 50 items and skips anything already tagged, so you can stop and re-run safely.
Failed items go to data/tag_errors.csv and are retried on the next run.

python tag.py --limit 50                 # test run on 50 items
python tag.py                            # everything
python tag.py --max-per-source 4000      # cap the biggest source (random sample, seed 42)
On the free Gemini tier, items are sent 15 per request (TAG_BATCH_SIZE in .env).
"""
import os, argparse, threading
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import DATA_DIR, TAG_BATCH_SIZE, LLM_PROVIDER
from tagger import tag_batch

OUT = f"{DATA_DIR}/tagged.csv"
ERR = f"{DATA_DIR}/tag_errors.csv"
_lock = threading.Lock()

def _append(rows, path):
    if not rows:
        return
    df = pd.DataFrame(rows)
    with _lock:
        if os.path.exists(path):
            old_cols = pd.read_csv(path, nrows=0).columns.tolist()
            df = df.reindex(columns=old_cols + [c for c in df.columns if c not in old_cols])
            if len(df.columns) > len(old_cols):          # new column appeared: rewrite file
                pd.concat([pd.read_csv(path, low_memory=False), df]).to_csv(path, index=False)
                return
            df.to_csv(path, mode="a", header=False, index=False)
        else:
            df.to_csv(path, index=False)

def main(limit=None, max_per_source=None, workers=4):
    src = pd.read_csv(f"{DATA_DIR}/filtered.csv", low_memory=False)
    if max_per_source:
        src = pd.concat([g.sample(min(len(g), max_per_source), random_state=42)
                         for _, g in src.groupby("source")])
    done = set(pd.read_csv(OUT, usecols=["id"])["id"].astype(str)) if os.path.exists(OUT) else set()
    todo = src[~src["id"].astype(str).isin(done)]
    if limit:
        todo = todo.head(limit)
    print(f"Already tagged: {len(done):,} | to tag now: {len(todo):,}")
    if os.path.exists(ERR):
        os.remove(ERR)

    rows = [r.to_dict() for _, r in todo.iterrows()]
    batches = [rows[i:i + TAG_BATCH_SIZE] for i in range(0, len(rows), TAG_BATCH_SIZE)]
    print(f"Provider: {LLM_PROVIDER} | {len(batches):,} requests of up to {TAG_BATCH_SIZE} items")
    ok_buf, err_buf, n_ok, n_err, n_done = [], [], 0, 0, 0
    def work(batch):
        return batch, tag_batch([b["text"] for b in batch])
    with ThreadPoolExecutor(workers) as ex:
        futures = [ex.submit(work, b) for b in batches]
        for i, f in enumerate(as_completed(futures), 1):
            batch, results = f.result()
            for row, tags in zip(batch, results):
                if "error" in tags:
                    err_buf.append({"id": row["id"], "source": row["source"], "error": tags["error"]})
                    n_err += 1
                else:
                    tags.pop("id", None); tags.pop("source", None); tags.pop("text", None)
                    ok_buf.append({**row, **tags})
                    n_ok += 1
            n_done += len(batch)
            if len(ok_buf) >= 50 or i == len(futures):
                _append(ok_buf, OUT); _append(err_buf, ERR)
                ok_buf, err_buf = [], []
                print(f"  {n_done}/{len(rows)}  ok={n_ok} errors={n_err}", flush=True)
    print(f"Done. tagged.csv now has {len(done) + n_ok:,} rows. Errors this run: {n_err}"
          + (" (re-run tag.py to retry them)" if n_err else ""))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--max-per-source", type=int)
    ap.add_argument("--workers", type=int, default=2 if LLM_PROVIDER == "gemini" else 4)
    a = ap.parse_args()
    main(a.limit, a.max_per_source, a.workers)
