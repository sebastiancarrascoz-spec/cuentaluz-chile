"""Respaldo trazable de fuentes públicas. No publica precios ni llama a los scrapers.

Uso: python scripts/source_repository.py archivo_de_solicitudes.json
Las solicitudes contienen id, url, clase y proveedor; las URL deben haberse
identificado en páginas oficiales. Los archivos se guardan por hash, sin sustituir
versiones anteriores. No procesa boletas privadas.
"""
import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "fuentes_nacionales"
OUT.mkdir(parents=True, exist_ok=True)


def fetch(item):
    record = {**item, "consultado_utc": datetime.now(timezone.utc).isoformat()}
    try:
        method = item.get("metodo", "GET")
        if method not in ("GET", "POST"):
            raise ValueError("Método no permitido para una consulta documental.")
        response = requests.request(method, item["url"], data=item.get("datos") if method == "POST" else None,
            timeout=(15, 60), headers={"User-Agent": "CuentaLuz/2.0 (investigación de pliegos públicos)"})
        record.update(http=response.status_code, url_final=response.url)
        response.raise_for_status()
        body = response.content
        if len(body) > 100 * 1024 * 1024:
            raise ValueError("Archivo superior a 100 MiB; requiere revisión de descarga.")
        content_type = response.headers.get("Content-Type", "")
        ext = ".pdf" if body.startswith(b"%PDF") else ".zip" if body.startswith(b"PK") else ".xls" if body.startswith(bytes.fromhex("D0CF11E0")) else ".html" if "html" in content_type else ".json" if "json" in content_type else ".bin"
        if item.get("clase") == "pliego" and ext not in (".pdf", ".zip", ".xls"):
            raise ValueError("La URL del pliego no entregó PDF, ZIP o Excel reconocible.")
        sha = hashlib.sha256(body).hexdigest()
        name = re.sub(r"[^a-zA-Z0-9_-]", "_", item["id"])
        path = OUT / (name + "_" + sha[:12] + ext)
        if not path.exists():
            path.write_bytes(body)
        record.update(estado="respaldado", sha256=sha, bytes=len(body), tipo=content_type, archivo=path.relative_to(ROOT).as_posix())
        if ext == ".html":
            soup = BeautifulSoup(body.decode("utf-8", errors="replace"), "html.parser")
            if any(t in soup.get_text(" ", strip=True).lower() for t in ("pardon our interruption", "access denied", "verify you are human", "request rejected")):
                record.update(estado="bloqueado", error="La fuente entregó una página de control de acceso, no el contenido solicitado.")
            record["enlaces"] = [{"texto": a.get_text(" ", strip=True), "url": urljoin(response.url, a["href"])} for a in soup.select("a[href]") if urlsplit(urljoin(response.url, a["href"])).scheme in ("http", "https")]
    except Exception as exc:
        record.update(estado="error", error=str(exc))
    print(json.dumps({k: record.get(k) for k in ("id", "estado", "bytes", "error")}, ensure_ascii=True), flush=True)
    return record


def main():
    tasks = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
    manifest_path = OUT / "manifest.json"
    records = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
    with ThreadPoolExecutor(max_workers=5) as pool:
        for record in pool.map(fetch, tasks):
            records.append(record)
            manifest_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"solicitudes": len(tasks), "respaldos_acumulados": sum(r["estado"] == "respaldado" for r in records)}, ensure_ascii=True))


if __name__ == "__main__":
    main()
