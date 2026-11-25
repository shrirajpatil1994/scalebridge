"""Collect published CAG audit reports on Maharashtra from the public listing (state filter 79).
Polite: 1 request/sec. Public pages only."""
import re, html, json, sys, time, urllib.request, urllib.parse
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read().decode("utf8", "ignore")
def clean(s): return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()
rows, seen = [], set()
pages = int(sys.argv[1]) if len(sys.argv) > 1 else 6
for p in range(1, pages + 1):
    q = "ts=allwords&title=&gt=&udt=&state=&state%5B%5D=79&lbt=&sector=&report_type=&od=&yrf=&yrt=&page=" + str(p)
    h = get("https://cag.gov.in/en/audit-report?" + q)
    for m in re.finditer(r'href="[^"]*?/en/audit-report/details/(\d+)"[^>]*>(.*?)</a>', h, re.S):
        rid, title = m.group(1), clean(m.group(2))
        if rid in seen or not title: continue
        seen.add(rid); rows.append({"id": rid, "title": title})
    time.sleep(1)
json.dump(rows, open("data/cag_listing.json", "w"), indent=1)
for r in rows: print(r["id"], r["title"][:140])
print(len(rows), "reports")
