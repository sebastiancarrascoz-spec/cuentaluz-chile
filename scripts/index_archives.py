"""Extrae documentos de ZIP a rutas controladas y registra cada huella."""
import hashlib
import json
import re
import zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/fuentes_nacionales"
records = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
members = []
for r in records:
    if r.get("estado") != "respaldado" or not r.get("archivo", "").endswith(".zip"):
        continue
    destination = (OUT / "extraidos" / r["sha256"][:12]).resolve()
    with zipfile.ZipFile(ROOT / r["archivo"]) as z:
        if sum(m.file_size for m in z.infolist()) > 150 * 1024 * 1024:
            raise ValueError("ZIP descomprimido demasiado grande")
        for m in z.infolist():
            if m.is_dir() or Path(m.filename).suffix.lower() not in (".pdf", ".xlsx", ".xls"):
                continue
            file = (destination / m.filename).resolve()
            if not file.is_relative_to(destination):
                raise ValueError("Ruta no admisible en ZIP")
            body = z.read(m)
            sha = hashlib.sha256(body).hexdigest()
            file.parent.mkdir(parents=True, exist_ok=True)
            if not file.exists():
                file.write_bytes(body)
            provider = next((id for name, id in [("edelaysen", "edelaysen"), ("frontel", "frontel"), ("luz osorno", "luzosorno"), ("saesa", "saesa")] if name in m.filename.lower()), r["proveedor"])
            members.append({"archivo": file.relative_to(ROOT).as_posix(), "nombre_zip": m.filename,
                "sha256": sha, "sha256_zip": r["sha256"], "url": r["url"], "proveedor": provider,
                "bytes": len(body), "estado": "respaldado_en_zip", "clase": "documento_extraido"})
(OUT / "miembros_zip.json").write_text(json.dumps(members, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"documentos_extraidos": len(members), "bytes": sum(m["bytes"] for m in members)}, ensure_ascii=True))
