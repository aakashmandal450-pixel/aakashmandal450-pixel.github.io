"""Refresh metrics.json with the Accesses and Citations counts shown on the
Springer article page. If the page can't be read, citations fall back to
Crossref, and any value that can't be found keeps its previous number."""
import json, re, datetime, urllib.request

DOI = "10.1007/s44290-025-00176-1"
URL = f"https://link.springer.com/article/{DOI}"
PATH = "metrics.json"

def get(url, accept="text/html"):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept": accept, "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def num(pattern, text):
    m = re.search(pattern, text, re.I)
    return int(m.group(1).replace(",", "")) if m else None

with open(PATH) as f:
    data = json.load(f)

acc = cit = None
try:
    html = re.sub(r"<[^>]+>", " ", get(URL))
    html = re.sub(r"\s+", " ", html)
    acc = num(r"([\d,]+)\s*Accesses", html)
    cit = num(r"([\d,]+)\s*Citations", html)
    print("Springer:", acc, "accesses,", cit, "citations")
except Exception as e:
    print("Springer page not readable:", e)

if cit is None:
    try:
        cr = json.loads(get(f"https://api.crossref.org/works/{DOI}", "application/json"))
        cit = cr["message"]["is-referenced-by-count"]
        print("Crossref citations:", cit)
    except Exception as e:
        print("Crossref not readable:", e)

changed = False
for key, val in (("accesses", acc), ("citations", cit)):
    if isinstance(val, int) and val > 0 and val != data.get(key):
        data[key] = val
        changed = True
if acc or cit:
    data["updated"] = datetime.date.today().isoformat()
    changed = True

if changed:
    with open(PATH, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
print(json.dumps(data))
