import pytest
from starlette.testclient import TestClient
from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("path", ["/", "/comunas", "/metodologia", "/health/live", "/health/ready", "/static/css/custom.css", "/static/js/main.js", "/robots.txt", "/sitemap.xml"])
def test_paginas_y_recursos(client, path):
    r = client.get(path)
    assert r.status_code == 200
    assert r.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize("dist", ["enel", "cge", "chilquinta", "frontel"])
def test_estimacion_formulario(client, dist):
    r = client.post("/calcular", data={"kwh_directo": "250", "distribuidora": dist})
    assert r.status_code == 200
    assert "referencia histórica" in r.text
    assert "saving-slider" in r.text
    assert r.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "1e309", "10001", "texto"])
def test_form_rechaza_consumos_invalidos(client, value):
    r = client.post("/calcular", data={"kwh_directo": value})
    assert r.status_code == 422
    assert 'role="alert"' in r.text


def test_sin_fallback_de_distribuidora(client):
    assert client.post("/calcular", data={"kwh_directo": "250", "distribuidora": "inventada"}).status_code == 422


def test_bt2_no_publica_resultado(client):
    assert client.post("/calcular", data={"kwh_directo": "250", "tarifa": "BT2"}).status_code == 422


def test_aparatos_y_dias(client):
    r = client.post("/calcular", data={"modo": "aparatos", "dias": "10", "aparato_tv": "on", "horas_tv": "5"})
    assert r.status_code == 200
    assert '5.0 kWh' in r.text
    assert client.post("/calcular", data={"modo": "aparatos", "aparato_tv": "on", "horas_tv": "25"}).status_code == 422
    assert client.post("/calcular", data={"modo": "aparatos", "aparato_tv": "on", "horas_tv": "nan"}).status_code == 422


def test_precios_personalizados_aritmetica_y_ahorro(client):
    r = client.post("/api/estimar", json={"kwh": 250, "fuente": "personalizada", "precio_kwh": 240, "cargo_fijo": 750, "boleta_actual": 65000})
    assert r.status_code == 200
    d = r.json()
    assert d["total"] == 60750
    assert d["diferencia_boleta"] == 4250
    assert d["escenarios"][1]["total"] == 48750
    assert d["escenarios"][1]["ahorro"] == 12000
    assert sum(c["valor"] for c in d["componentes"]) == d["total"]


@pytest.mark.parametrize("data", [{"kwh": 0}, {"kwh": 250, "dias": 0}, {"kwh": 250, "dias": 63},
    {"kwh": 250, "distribuidora": "metadata"}, {"kwh": 250, "tarifa": "BT2"},
    {"kwh": 250, "fuente": "personalizada"}, {"kwh": 250, "precio_kwh": -1}])
def test_api_validacion(client, data):
    assert client.post("/api/estimar", json=data).status_code == 422


def test_limite_cuerpo(client):
    assert client.post("/api/estimar", content="x" * 32769).status_code == 413


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity"])
def test_json_no_finito_no_causa_error_500(client, number):
    r = client.post("/api/estimar", content='{"kwh":' + number + '}', headers={"Content-Type": "application/json"})
    assert r.status_code == 422
    assert r.json()["detail"][0]["campo"] == "body.kwh"


def test_host_invalido(client):
    assert client.get("/", headers={"host": "evil.example"}).status_code == 400


def test_captacion_y_gps_no_expuestos(client):
    assert client.post("/api/newsletter", json={"email": "test@example.org"}).status_code == 404
    assert client.get("/api/gis/distribuidora?lat=-33&lon=-70").status_code == 404


def test_produccion_bloquea_catalogo_sin_aprobar(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    assert client.post("/api/estimar", json={"kwh": 250}).status_code == 503
    assert client.post("/calcular", data={"kwh_directo": "250"}).status_code == 503
    assert client.post("/api/estimar", json={"kwh": 250, "fuente": "personalizada", "precio_kwh": 240, "cargo_fijo": 750}).status_code == 200


def test_no_scripts_terceros_ni_datos_persistidos(client):
    r = client.get("/")
    assert "cdn.tailwindcss.com" not in r.text
    assert "fonts.googleapis.com" not in r.text
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
