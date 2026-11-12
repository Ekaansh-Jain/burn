"""Step 1c: re-fetch ICRA reports via their direct PDF URL and retry CRISIL reports that were rate-limited."""
import re
import time

import pandas as pd
import requests

from download_reports import UA, to_text

idx = pd.read_csv("data/report_index.csv")
stats = {"icra_fixed": 0, "icra_fail": 0, "crisil_ok": 0, "crisil_fail": 0}
for i, row in idx.iterrows():
    try:
        if row["agency"] == "icra" and row["chars"] < 8000:
            m = re.search(r"Id=(\d+)", row["url"])
            if not m:
                continue
            r = requests.get(f"https://www.icra.in/Rating/ShowRationalReportFilePdfViewer/{m.group(1)}",
                             headers=UA, timeout=45)
            if r.status_code == 200 and r.content[:4] == b"%PDF":
                txt = to_text(r.content, "pdf")
                open(row["file"], "w").write(txt)
                idx.loc[i, ["chars", "status"]] = [len(txt), 200]
                stats["icra_fixed"] += 1
            else:
                stats["icra_fail"] += 1
            time.sleep(0.4)
        elif row["agency"] == "crisil" and row["chars"] < 1500:
            for attempt in range(3):
                r = requests.get(row["url"], headers=UA, timeout=45)
                if r.status_code == 200:
                    txt = to_text(r.content, r.headers.get("content-type", ""))
                    open(row["file"], "w").write(txt)
                    idx.loc[i, ["chars", "status"]] = [len(txt), 200]
                    stats["crisil_ok"] += 1
                    break
                time.sleep(10 * (attempt + 1))
            else:
                stats["crisil_fail"] += 1
            time.sleep(3)
    except Exception as e:  # keep going on network errors
        print("err", row["symbol"], row["agency"], type(e).__name__, flush=True)
    if (i + 1) % 50 == 0:
        idx.to_csv("data/report_index.csv", index=False)
        print(i + 1, stats, flush=True)

idx.to_csv("data/report_index.csv", index=False)
idx["ok"] = idx["chars"] > 1500
print(stats)
print(idx.groupby("agency").agg(n=("ok", "size"), ok=("ok", "sum"), med_chars=("chars", "median")))
