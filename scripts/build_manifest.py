"""Build data/manifest.json from (a) CAG report detail pages and (b) direct public PDF links, then download.
Public CAG publications only. 1 request/sec."""
import re, html, json, time, urllib.request, urllib.parse
from pathlib import Path
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
RAW = Path("data/raw"); RAW.mkdir(parents=True, exist_ok=True)
def get(u, binary=False):
    r = urllib.request.urlopen(urllib.request.Request(urllib.parse.quote(u, safe=":/?=&%"), headers=UA), timeout=90).read()
    return r if binary else r.decode("utf8", "ignore")
def clean(s): return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s))).strip()

DETAIL_IDS = ["117101", "122175", "125474", "125414", "125459", "118969", "122158", "121872", "123523", "125594"]
DIRECT = [
 ("cidco-2019", "PSU Report 5 of 2019 (Maharashtra): Performance audit of infrastructure development by CIDCO", "https://cag.gov.in/uploads/download_audit_report/2019/Chapter_4_Performance_Audit_on_Infrastructure_Development_by_City_and_Industrial_Development_Corporation_Limited_other_than_Power_Sector_of_Report_no_5_of_2019_P.pdf"),
 ("monorail-2015", "Maharashtra Report 4 of 2015, Chapter 3 (includes Mumbai Monorail, MMRDA)", "https://cag.gov.in/uploads/download_audit_report/2015/Maharashtra_Report_4_2015_chap_3.PDF"),
 ("slum-2014", "Maharashtra Report 4 of 2014, Chapter 3 (includes Slum Improvement Board, MHADA)", "https://cag.gov.in/uploads/download_audit_report/2014/Maharashtra_Report_4_2014_chap_3.pdf"),
 ("mcgm-swd-2014", "Maharashtra Local Bodies Report 6 of 2014, Chapter 4 (includes MCGM storm water drains)", "https://cag.gov.in/uploads/download_audit_report/2014/Maharashtra_Report_6_2014_Chap_4.pdf"),
 ("lb-atir-2017", "Annual Technical Inspection Report on Local Bodies 2017 (Maharashtra), Chapter 3 compliance paragraphs", "https://www.cag.gov.in/uploads/download_audit_report/2017/Chapter_3_Compliance_Audit_Paragraphs_of_Report_of_2017_-_Annual_Technical_Inspection_on_Local_BodiesGovernment_of_Maharashtra.pdf"),
 ("psu-2017", "PSU Report 2 of 2017 (Maharashtra), Chapter 3 compliance paragraphs", "https://cag.gov.in/uploads/download_audit_report/2017/Maharashtra Chapter_3_Compliance_Audit_Paragraphs_Report_No_2_of_2017_on_PSUs.pdf"),
 ("psu-2018", "PSU Report 4 of 2018 (Maharashtra), Chapter 3 compliance paragraphs", "https://cag.gov.in/uploads/download_audit_report/2017/Chapter_3_Compliance_Audit_Paragraphs_of_Report_No_4_of_2018_-_Public_Sector_Undertakings_Government_of_Maharashtra.pdf"),
]
manifest = []
for rid in DETAIL_IDS:
    try: h = get(f"https://cag.gov.in/en/audit-report/details/{rid}")
    except Exception as e: print("ERR detail", rid, e); continue
    t = clean(re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S))
    gb = t.find("Go Back"); head = t[gb:gb+1500]
    if "Maharashtra" not in head: print("skip (not Maharashtra)", rid, head[:120]); time.sleep(1); continue
    title = re.sub(r"^Go Back\s+\w+\s+Maharashtra\s+", "", head.split(" Date on which")[0])[:220]
    tabled = (re.search(r"Report Tabled\s*:?\s*\w{3} (\d{1,2} \w{3}, \d{4})", head) or [None, ""])[1]
    pdfs = list(dict.fromkeys(p.replace("&amp;", "&") for p in re.findall(r'https://d1jmc0u14z2tmp\.cloudfront\.net/uploads/download_audit_report/[^"\'<>]+?\.pdf', h)))
    manifest.append({"id": rid, "title": title, "tabled": tabled, "source": f"https://cag.gov.in/en/audit-report/details/{rid}", "urls": pdfs})
    print("MH", rid, tabled, len(pdfs), title[:100]); time.sleep(1)
for rid, title, url in DIRECT:
    manifest.append({"id": rid, "title": title, "tabled": "", "source": url, "urls": [url]})
# download
for rep in manifest:
    rep["files"] = []
    for i, u in enumerate(rep["urls"]):
        fn = f"{rep['id']}_{i:02d}.pdf"; dest = RAW / fn
        if not dest.exists():
            try: dest.write_bytes(get(u, binary=True)); time.sleep(1)
            except Exception as e: print("ERR pdf", u[-60:], e); continue
        if dest.stat().st_size > 1000: rep["files"].append(fn)
json.dump(manifest, open("data/manifest.json", "w"), indent=1)
print(len(manifest), "reports;", sum(len(r["files"]) for r in manifest), "PDF files")
