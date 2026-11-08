"""Planifica descargas solo desde enlaces observados, conservando su contexto."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, unquote
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/fuentes_nacionales"
records = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
existing = {r["url"] for r in records if r["estado"] == "respaldado" or r.get("http") in (403, 404)}
tasks = {}
for record in records:
    if record.get("estado") != "respaldado" or not record.get("archivo", "").endswith(".html"):
        continue
    soup = BeautifulSoup((ROOT / record["archivo"]).read_bytes().decode("utf-8", errors="replace"), "html.parser")
    for a in soup.select("a[href]"):
        url = urljoin(record["url_final"], a["href"])
        context = a.find_parent("tr") or a.find_parent("li") or a.parent
        text = context.get_text(" ", strip=True)[:600]
        hint = unquote(url) + " " + text
        document = re.search(r"\.(pdf|xls|xlsx|zip)(\?|$)", url, re.I) or "/descargar/" in url
        relevant = "2026" in hint or (record["id"] == "sec_tarifas_suministro" and "2024" in hint)
        if document and relevant and url not in existing:
            tasks[url] = {"id": record["proveedor"] + "_doc_" + hashlib.sha256(url.encode()).hexdigest()[:12],
                "proveedor": record["proveedor"], "clase": "pliego" if record["proveedor"] not in ("cne", "sec") else "normativa",
                "url": url, "origen": record["url"], "contexto": text}
(OUT / "descargas_planificadas.json").write_text(json.dumps(list(tasks.values()), ensure_ascii=False, indent=2), encoding="utf-8")
from collections import Counter
print(json.dumps({"descargas": len(tasks), "por_proveedor": dict(Counter(t["proveedor"] for t in tasks.values()))}, ensure_ascii=True))
