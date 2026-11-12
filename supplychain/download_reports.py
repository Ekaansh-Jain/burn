"""Step 1b: download every credit-rating report and convert it to plain text.

Input:  data/rating_links.json
Output: data/text/<SYMBOL>__<date>__<agency>.txt  and data/report_index.csv
"""
import csv
import io
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pdfplumber
import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124 Safari/537.36"}
NOYEAR_RE = re.compile(r"(\d{1,2} \w{3})\b(?! \d{4})")
os.makedirs("data/text", exist_ok=True)


def fix_dates(links: dict) -> dict:
    """Screener omits the year for current-year (2026) updates."""
    for v in links.values():
        for r in v.get("ratings", []):
            if not r["date"]:
                m = NOYEAR_RE.search(r["title"])
                if m:
                    r["date"] = datetime.strptime(m.group(1) + " 2026", "%d %b %Y").date().isoformat()
    return links


def to_text(content: bytes, ctype: str) -> str:
    if content[:4] == b"%PDF" or "pdf" in (ctype or ""):
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            return "\n".join((p.extract_text() or "") for p in pdf.pages[:12])
    soup = BeautifulSoup(content, "lxml")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    return soup.get_text("\n", strip=True)


def fetch(sym: str, r: dict) -> dict:
    fn = f"data/text/{sym.replace('&', 'and')}__{r['date']}__{r['agency']}.txt"
    row = {"symbol": sym, "date": r["date"], "agency": r["agency"], "url": r["url"], "file": fn,
           "status": None, "chars": 0}
    if os.path.exists(fn) and os.path.getsize(fn) > 500:
        row.update(status="cached", chars=os.path.getsize(fn))
        return row
    try:
        resp = requests.get(r["url"], headers=UA, timeout=45)
        row["status"] = resp.status_code
        if resp.status_code == 200:
            txt = to_text(resp.content, resp.headers.get("content-type", ""))
            row["chars"] = len(txt)
            with open(fn, "w") as f:
                f.write(txt)
    except Exception as e:  # keep going; record the failure for the coverage report
        row["status"] = f"err:{type(e).__name__}"
    time.sleep(0.5)
    return row


def main():
    links = fix_dates(json.load(open("data/rating_links.json")))
    json.dump(links, open("data/rating_links.json", "w"), indent=1)
    jobs = [(s, r) for s, v in links.items() for r in v.get("ratings", []) if r.get("url")]
    rows = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futs = [ex.submit(fetch, s, r) for s, r in jobs]
        for i, f in enumerate(as_completed(futs)):
            rows.append(f.result())
            if (i + 1) % 50 == 0:
                print(f"{i+1}/{len(jobs)} done", flush=True)
    with open("data/report_index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
