"""Prueba un proceso real con configuración de producción y lo cierra al finalizar."""
import json
import os
import subprocess
import time
from pathlib import Path
import httpx2 as httpx
from verify_runtime import verify

ROOT = Path(__file__).resolve().parents[1]
env = {**os.environ, "APP_ENV": "production", "ALLOWED_HOSTS": "127.0.0.1,localhost", "DATABASE_URL": "sqlite:///" + (ROOT / "artifacts" / "smoke-production.db").as_posix()}
python = ROOT / ".venv" / "Scripts" / "python.exe"
process = subprocess.Popen([str(python), "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8019", "--no-access-log"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
try:
    with httpx.Client(base_url="http://127.0.0.1:8019", timeout=3) as client:
        for attempt in range(30):
            try:
                response = client.get("/health/ready")
                if response.status_code == 200:
                    break
            except httpx.HTTPError:
                time.sleep(0.2)
        else:
            raise RuntimeError("El candidato de producción no inició.")
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
        assert client.get("/", headers={"host": "evil.example"}).status_code == 400
        assert 'value="personalizada" selected' in client.get("/").text
        assert client.post("/api/estimar", json={"kwh": 250}).status_code == 503
        result = client.post("/api/estimar", json={"kwh": 250, "fuente": "personalizada", "precio_kwh": 240, "cargo_fijo": 750})
        assert result.status_code == 200 and result.json()["total"] == 60750
        assert result.headers["cache-control"] == "no-store"
        assert "max-age=" in result.headers["strict-transport-security"]
        consolidated=verify("http://127.0.0.1:8019")
        summary = {"produccion": "comprobada en proceso local", "catalogo_no_aprobado": "503", "precios_propios": "200; total 60750", "cuenta_consolidada":consolidated,"hosts": "rechazo 400", "documentacion_api": "404", "despliegue_remoto": "no realizado", "docker": "no disponible"}
        (ROOT / "artifacts" / "production-smoke.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=True))
finally:
    process.terminate()
    process.communicate(timeout=10)
