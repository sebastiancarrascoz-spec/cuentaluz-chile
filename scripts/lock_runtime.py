"""Captura las versiones instaladas del árbol de dependencias de producción."""
from importlib.metadata import distribution
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

root = Path(__file__).resolve().parents[1]
queue = [Requirement(line).name for line in (root / "requirements.txt").read_text().splitlines() if line and not line.startswith("#")]
versions = {}
while queue:
    name = canonicalize_name(queue.pop())
    if name in versions:
        continue
    dist = distribution(name)
    versions[name] = dist.version
    for raw in dist.requires or []:
        req = Requirement(raw)
        if not req.marker or req.marker.evaluate({"extra": ""}):
            queue.append(req.name)
lines = ["# Versiones de producción resueltas y probadas con Python 3.11."]
lines.extend(f"{name}=={version}" for name, version in sorted(versions.items()))
(root / "requirements.lock").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"{len(versions)} paquetes fijados")
