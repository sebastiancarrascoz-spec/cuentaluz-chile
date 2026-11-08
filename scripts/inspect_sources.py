"""Inventario legible de enlaces de los portales respaldados."""
import json
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup
ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "artifacts/fuentes_nacionales/manifest.json").read_text(encoding="utf-8"))
for r in manifest:
    if len(sys.argv) > 1 and not any(s in r["id"] for s in sys.argv[1:]):
        continue
    print(r["id"], r["estado"])
    if r.get("archivo", "").endswith(".html"):
        soup = BeautifulSoup((ROOT / r["archivo"]).read_bytes().decode("utf-8", errors="replace"), "html.parser")
        for a in soup.select("a[href]"):
            href = a["href"]
            if any(x in href.lower() for x in (".pdf", ".xls", ".zip", "tarif", "2026", "5t", "suministro")):
                context = a.find_parent("tr") or a.find_parent("li") or a.parent
                title = context.get_text(" ", strip=True)[:200]
                print(json.dumps({"texto": title, "url": href}, ensure_ascii=True))
