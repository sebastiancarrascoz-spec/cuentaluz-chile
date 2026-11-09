import hashlib
import json
from pathlib import Path


def test_integridad_del_lector_y_su_worker_local():
    root = Path(__file__).resolve().parents[1] / "static/vendor/pdfjs"
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "6.5.438"
    for name, sha in manifest["sha256"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == sha
    assert (root / "LICENSE").exists()
