"""Step 1a: collect dated credit-rating report links for each supplier from Screener company pages.

Screener's robots.txt allows /company/<SYMBOL>/ pages; we fetch one page per company with a delay.
Output: data/rating_links.json  {symbol: {"market_cap_cr": float|None, "ratings": [{date, agency, title, url}]}}
"""
import json
import re
import time
import urllib.parse
from datetime import datetime

import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124 Safari/537.36"}
DATE_RE = re.compile(r"(\d{1,2} \w{3} \d{4})")
AGENCY_RE = re.compile(r"from (\w+)", re.I)


def parse_page(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    out = {"market_cap_cr": None, "ratings": []}
    for li in soup.select("#top-ratios li"):
        name = li.select_one(".name")
        if name and "Market Cap" in name.get_text():
            num = li.select_one(".number")
            if num:
                try:
                    out["market_cap_cr"] = float(num.get_text().replace(",", ""))
                except ValueError:
                    pass
    for div in soup.find_all("div"):
        h = div.find("h3", recursive=False)
        if h and "credit rating" in h.get_text(strip=True).lower():
            for a in div.find_all("a"):
                text = a.get_text(" ", strip=True)
                d = DATE_RE.search(text)
                ag = AGENCY_RE.search(text)
                date = datetime.strptime(d.group(1), "%d %b %Y").date().isoformat() if d else None
                out["ratings"].append({"date": date, "agency": ag.group(1).lower() if ag else None,
                                       "title": text, "url": a.get("href")})
            break
    return out


def main():
    uni = json.load(open("data/universe.json"))
    result = {}
    for i, sym in enumerate(uni["suppliers"]):
        url = f"https://www.screener.in/company/{urllib.parse.quote(sym)}/"
        try:
            r = requests.get(url, headers=UA, timeout=30)
            if r.status_code == 200:
                result[sym] = parse_page(r.text)
            else:
                result[sym] = {"error": r.status_code, "ratings": []}
        except Exception as e:  # network hiccup: record and continue
            result[sym] = {"error": str(e), "ratings": []}
        n = len(result[sym].get("ratings", []))
        print(f"{i+1:3d}/{len(uni['suppliers'])} {sym:12s} ratings={n} mcap={result[sym].get('market_cap_cr')}", flush=True)
        time.sleep(2.0)
    json.dump(result, open("data/rating_links.json", "w"), indent=1)


if __name__ == "__main__":
    main()
