"""Copia la versión fijada de PDF.js y conserva licencia y huellas."""
import hashlib
import json
import shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
package = ROOT / ".qa/node_modules/pdfjs-dist"
version = "6.5.438"
assert json.loads((package / "package.json").read_text())["version"] == version
lock = json.loads((ROOT / ".qa/package-lock.json").read_text())["packages"]["node_modules/pdfjs-dist"]
expected = "sha512-vg8Pw1x+AFKy4AMDvhuWl5cOYV8d698UoEANoFFhc79hqXDnZQqnOXoxw3HG907WHOg1JYOvLhP756boddFxpA=="
assert lock["integrity"] == expected
out = ROOT / "static/vendor/pdfjs"
out.mkdir(parents=True, exist_ok=True)
files = {}
for source, target in [("build/pdf.min.mjs", "pdf.min.mjs"), ("build/pdf.worker.min.mjs", "pdf.worker.min.mjs"), ("LICENSE", "LICENSE")]:
    shutil.copyfile(package / source, out / target)
    files[target] = hashlib.sha256((out / target).read_bytes()).hexdigest()
metadata = {"nombre":"pdfjs-dist", "version":version, "licencia":"Apache-2.0",
    "origen":lock["resolved"], "integridad_npm":expected, "sha256":files,
    "reproduccion":"npm install --prefix .qa --save-exact --ignore-scripts --omit=optional pdfjs-dist@6.5.438; python scripts/vendor_pdfjs.py"}
(out / "manifest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"version":version, "archivos":len(files)}))
