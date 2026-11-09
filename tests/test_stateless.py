import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]


def test_vercel_requirements_are_flat_and_match_container_lock():
    def packages(name):
        return [line.strip() for line in (ROOT/name).read_text(encoding='utf-8').splitlines() if line.strip() and not line.startswith('#')]
    assert packages('requirements.txt')==packages('requirements.lock')
    assert all('==' in line and not line.startswith('-') for line in packages('requirements.txt'))


def run(code, **extra):
    env={**os.environ,"APP_STORAGE":"none","APP_ENV":"production","VERCEL":"1","VERCEL_ENV":"preview",
        "VERCEL_URL":"cuentaluz-prueba.vercel.app", **extra}
    env.pop("DATABASE_URL",None);env.pop("ALLOWED_HOSTS",None)
    return subprocess.run([sys.executable,"-c",code],cwd=ROOT,env=env,text=True,capture_output=True)


@pytest.mark.parametrize('platform_env,preview_flag',[('preview','0'),('production','1')])
def test_stateless_starts_calculates_and_never_connects_to_database(platform_env,preview_flag):
    result=run('''
from fastapi.testclient import TestClient
import main
def forbidden(*a,**k):raise AssertionError("No debe usar almacenamiento")
main.engine.connect=forbidden
main.Base.metadata.create_all=forbidden
with TestClient(main.app,base_url="https://cuentaluz-prueba.vercel.app") as c:
    assert c.get("/health/ready").json()["almacenamiento"]=="sin_persistencia"
    assert c.get("/cuenta").status_code==200
    assert "Vista previa de pruebas" in c.get("/cuenta").text
    assert c.get("/cuenta").headers["x-robots-tag"]=="noindex, nofollow, noarchive"
    assert c.get("/robots.txt").text=="User-agent: *\\nDisallow: /\\n"
    assert c.post("/api/estimar",json={"kwh":250}).status_code==503
    r=c.post("/api/estimar",json={"kwh":250,"fuente":"personalizada","precio_kwh":240,"cargo_fijo":750})
    assert r.status_code==200 and r.json()["total"]==60750
    assert c.get("/",headers={"host":"evil.vercel.app"}).status_code==400
    assert c.get("/docs").status_code==404
print("ok")
''',VERCEL_ENV=platform_env,APP_PREVIEW=preview_flag)
    assert result.returncode==0,result.stderr


@pytest.mark.parametrize('host',['*.vercel.app','evil.example','https://cuentaluz.vercel.app','cuentaluz.vercel.app/path','cuentaluz.vercel.app.evil.example'])
def test_platform_host_must_be_an_exact_platform_assigned_hostname(host):
    result=run('import main',VERCEL_URL=host,VERCEL_BRANCH_URL='',VERCEL_PROJECT_PRODUCTION_URL='')
    assert result.returncode!=0 and 'ALLOWED_HOSTS' in result.stderr


def test_stateless_database_dependency_refuses_use():
    result=run('''
from database import get_db
try: next(get_db())
except RuntimeError: print("ok")
else: raise AssertionError("No debe devolver sesiones")
''')
    assert result.returncode==0,result.stderr
