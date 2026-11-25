"""Fetch CAG report detail pages, keep Maharashtra reports, record metadata + PDF links."""
import re, html, json, sys, time, urllib.request
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=40).read().decode("utf8","ignore")
def clean(s): return html.unescape(re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",s))).strip()
OTHER = re.compile(r"Assam|Nagaland|Madhya Pradesh|West Bengal|Gujarat|Odisha|Bihar|Karnataka|Kerala|Rajasthan|Uttar Pradesh|Uttarakhand|Himachal|Jammu|Goa|Andhra|Telangana|Tamil|Punjab|Haryana|Jharkhand|Chhattisgarh|Sikkim|Tripura|Meghalaya|Manipur|Mizoram|Arunachal|Delhi|GNCTD|Union Government|Union Territory|Puducherry|Ladakh|Ministry|Railway|Indirect Taxes|Direct Tax|Customs|Defence", re.I)
listing = json.load(open("data/cag_listing.json"))
out = []
import os
done = set()
if os.path.exists("data/cag_maharashtra.json"):
    out = json.load(open("data/cag_maharashtra.json")); done = {x["id"] for x in out}
for r in listing:
    if OTHER.search(r["title"]) or r["id"] in done: continue
    try: h = get(f"https://cag.gov.in/en/audit-report/details/{r['id']}")
    except Exception as e: print("ERR", r["id"], e); continue
    t = clean(re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S))
    st = re.search(r"State\s*:?\s*([A-Z][A-Za-z ]+?)\s+(?:Sector|Report Type|Date|Download|Union)", t)
    state = st.group(1).strip() if st else ("Maharashtra" if "Maharashtra" in t[:20000] else "?")
    tabled = (re.search(r"Date on which Report Tabled\s*:?\s*([A-Za-z]{3} \d{1,2} [A-Za-z]{3}, \d{4})", t) or [None,""])[1]
    pdfs = list(dict.fromkeys(p.replace("&amp;","&") for p in re.findall(r'https://d1jmc0u14z2tmp\.cloudfront\.net/uploads/download_audit_report/[^"\'\s<>]+\.pdf', h)))
    rec = {**r, "state": state, "tabled": tabled, "pdfs": pdfs}
    if re.search(r"Govern(or|ment) of Maharashtra|Brihanmumbai|Maharashtra", r["title"] + " " + t[t.find("Go Back"):t.find("Go Back")+3000]):
        out.append(rec); print("MH", r["id"], tabled, len(pdfs), r["title"][:100], flush=True)
        json.dump(out, open("data/cag_maharashtra.json","w"), indent=1)
    time.sleep(1)
json.dump(out, open("data/cag_maharashtra.json","w"), indent=1)
print(len(out), "Maharashtra reports")
