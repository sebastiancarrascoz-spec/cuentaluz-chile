"""Comprueba UTF-8 y la integridad del catálogo recuperado."""
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines()
new = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines()
checked = 0
for name in sorted(set(changed + new)):
    path = ROOT / name
    if not path.is_file():
        continue
    contents = path.read_text(encoding="utf-8-sig")
    assert "\ufffd" not in contents, name
    checked += 1
# PowerShell 5.1 necesita BOM para interpretar correctamente las tildes del script.
launcher = ROOT / "Iniciar-CuentaLuz.ps1"
launcher.write_text(launcher.read_text(encoding="utf-8-sig"), encoding="utf-8-sig")
original = subprocess.check_output(["git", "show", "master:config/tarifas.json"], cwd=ROOT)
current = (ROOT / "config" / "tarifas.json").read_bytes()
assert original == current, "El catálogo original cambió sin una revisión tarifaria."
print(f"Archivos UTF-8 comprobados: {checked}. Catálogo original conservado.")
print("SHA-256 catálogo:", hashlib.sha256(current).hexdigest())
