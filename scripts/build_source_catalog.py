"""Verifica los respaldos por SHA-256 y publica solo su inventario documental.

Los códigos detectados en texto son indicios de contenido, no modelos aprobados.
No accede a boletas privadas ni convierte automáticamente tablas en precios.
"""
import csv
import hashlib
import json
import re
from datetime import date
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit
import pymupdf
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/fuentes_nacionales"
records = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
members = json.loads((OUT / "miembros_zip.json").read_text(encoding="utf-8"))
documents = {}
indices, issues = [], []
for r in records + members:
    if r["estado"] not in ("respaldado", "respaldado_en_zip"):
        issues.append({k: r.get(k) for k in ("proveedor", "url", "estado", "http", "error")})
        continue
    path = ROOT / r["archivo"]
    body = path.read_bytes()
    if hashlib.sha256(body).hexdigest() != r["sha256"]:
        raise ValueError("Integridad incorrecta: " + str(path))
    if path.suffix == ".html":
        text = BeautifulSoup(body, "html.parser").get_text(" ", strip=True).lower()
        blocked = any(x in text for x in ("pardon our interruption", "access denied", "verify you are human", "request rejected"))
        indices.append({"proveedor": r["proveedor"], "url": r["url"], "estado": "bloqueado" if blocked else "indice_consultado"})
        if blocked:
            issues.append({"proveedor": r["proveedor"], "url": r["url"], "estado": "bloqueado", "error": "Página de control de acceso; no es un pliego."})
        continue
    if path.suffix not in (".pdf", ".xls", ".xlsx"):
        continue
    if r["sha256"] in documents:
        continue
    text, pages, codes = "", None, []
    if path.suffix == ".pdf":
        with pymupdf.open(path) as doc:
            pages = len(doc)
            text = "\n".join(p.get_text() for p in doc)
        codes = sorted(set(re.findall(r"\b(?:TRBT|TRAT|BT|AT)[ -]?(?:[1-6](?:\.[1-3])?[abAB]?|[1-6][aAbB]?)\b", text)))
    hint = r.get("contexto", "") + " " + r.get("nombre_zip", "") + " " + r["url"]
    documents[r["sha256"]] = {"proveedor": r["proveedor"], "url": r["url"],
        "archivo": r["archivo"], "sha256": r["sha256"], "bytes": len(body),
        "tipo": path.suffix.lstrip("."), "clase": r.get("clase"), "paginas": pages,
        "nombre_documental": unquote(r.get("nombre_zip") or "/".join(urlsplit(r["url"]).path.split("/")[-2:])),
        "opciones_detectadas": codes, "estado_calculo": "pendiente",
        "advertencia": "La detección textual no confirma vigencia, condiciones ni valores tarifarios."}
    if text:
        text_path = OUT / "texto" / (r["sha256"] + ".txt")
        text_path.parent.mkdir(exist_ok=True)
        text_path.write_text(text, encoding="utf-8")

items = list(documents.values())
result = {"fecha_revision": date.today().isoformat(), "documentos": items, "incidencias": issues,
    "indices": indices, "resumen": {"documentos_unicos": len(items),
        "por_tipo": dict(Counter(r["tipo"] for r in items)),
        "por_proveedor": dict(sorted(Counter(r["proveedor"] for r in items).items())),
        "opciones_detectadas": sorted({c for r in items for c in r["opciones_detectadas"]}),
        "modelos_aprobados": 0}}
(ROOT / "config/fuentes_nacionales.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
with (OUT / "indice_documental.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(items[0]), delimiter=";")
    writer.writeheader()
    writer.writerows({**r, "opciones_detectadas": " | ".join(r["opciones_detectadas"])} for r in items)
print(json.dumps(result["resumen"], ensure_ascii=True, indent=2))
