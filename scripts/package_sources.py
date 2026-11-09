"""Paquete local verificable de fuentes públicas. Excluye toda boleta privada."""
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts/fuentes_nacionales"
OUT = ROOT.parent / "cuentaluz-respaldos"
OUT.mkdir(exist_ok=True)
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
target = OUT / ("CuentaLuz-fuentes-publicas-" + stamp + ".zip")
paths = [p for p in SOURCE.rglob("*") if p.is_file() and "texto" not in p.relative_to(SOURCE).parts]
paths += list((ROOT / "config").glob("fuentes_*.json"))
paths += [ROOT / p for p in ("config/cobertura_nacional.json", "RESPALDOS_NACIONALES.md",
    "config/enel_macul_octubre_candidato.json", "requirements-sources.txt")]
paths += [p for p in (ROOT / "scripts").glob("*.py") if p.name in (
    "source_repository.py", "index_archives.py", "build_national_inventory.py", "build_source_catalog.py",
    "inspect_sources.py", "plan_source_downloads.py")]
entries = {}
with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for path in sorted(set(paths)):
        name = path.relative_to(ROOT).as_posix()
        body = path.read_bytes()
        entries[name] = hashlib.sha256(body).hexdigest()
        z.writestr(name, body)
    z.writestr("INTEGRIDAD.json", json.dumps(entries, ensure_ascii=False, indent=2).encode("utf-8"))
with zipfile.ZipFile(target) as z:
    for name, sha in entries.items():
        if hashlib.sha256(z.read(name)).hexdigest() != sha:
            raise ValueError("Error de integridad: " + name)
sha = hashlib.sha256(target.read_bytes()).hexdigest()
target.with_suffix(".zip.sha256").write_text(sha + "  " + target.name + "\n", encoding="utf-8")
result = {"archivo": str(target), "sha256":sha, "bytes":target.stat().st_size,
    "archivos_verificados":len(entries), "alcance":"Fuentes públicas; sin boletas privadas ni credenciales."}
(ROOT / "artifacts/paquete-fuentes.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=True))
