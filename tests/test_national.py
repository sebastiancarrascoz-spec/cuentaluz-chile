import json
from pathlib import Path
from decimal import Decimal
import pytest
from pydantic import ValidationError
from starlette.testclient import TestClient
from app.services.invoice_service import InvoiceInput, conciliar, peso
from main import app

ROOT = Path(__file__).resolve().parents[1]


def test_conciliacion_caso_anonimo_con_exento():
    entrada = InvoiceInput(lineas=[
        {"nombre": "Electricidad", "neto": "26300", "tratamiento": "afecto"},
        {"nombre": "Transporte", "neto": "2497", "tratamiento": "afecto"},
        {"nombre": "Administración", "neto": "614", "tratamiento": "afecto"},
        {"nombre": "Servicio público", "neto": "124", "tratamiento": "exento"}], total_documento=35123)
    r = conciliar(entrada)
    assert (r["neto_afecto"], r["iva"], r["exento"], r["total"], r["diferencia"]) == (29411, 5588, 124, 35123, 0)
    assert r["coincide"]


def test_impuesto_sobre_total_y_ajuste_no_tributa_nuevamente():
    entrada = InvoiceInput(lineas=[{"nombre": "Cargo", "neto": 10, "tratamiento": "afecto"}] * 2,
        total_documento=19, ajustes_finales=-5)
    assert conciliar(entrada)["total"] == 19
    assert peso(Decimal("2.5")) == 3
    assert peso(Decimal("-2.5")) == -3


@pytest.mark.parametrize("valor", ["NaN", "Infinity", "-1", "100000000001", "0.00001"])
def test_rechaza_importes_invalidos(valor):
    with pytest.raises(ValidationError):
        InvoiceInput(lineas=[{"nombre": "Cargo", "neto": valor, "tratamiento": "afecto"}], total_documento=0)


def test_directorio_no_inventa_concesionaria():
    data = json.loads((ROOT / "config/cobertura_nacional.json").read_text(encoding="utf-8"))
    cs = data["comunas"]
    assert len(cs) == len({c["cut"] for c in cs}) == 346
    assert len({c["region_codigo"] for c in cs}) == 16
    assert all(c["estado_calculo"] == "pendiente" for c in cs)
    assert sum(bool(c["concesionarias_cne"]) for c in cs) == 330
    assert not next(c for c in cs if c["nombre"] == "Camiña")["concesionarias_cne"]
    assert "EEPA" in next(c for c in cs if c["nombre"] == "Puente Alto")["concesionarias_cne"]
    assert "EDELMAG" in next(c for c in cs if c["nombre"] == "Punta Arenas")["concesionarias_cne"]


def test_nuevas_paginas_y_revision_formulario():
    with TestClient(app) as c:
        for path in ("/comunas", "/fuentes", "/revisar"):
            assert c.get(path).status_code == 200
        r = c.post("/revisar", data={"electricidad":26300, "transporte":2497,
            "administracion":614, "exentos":124, "total_documento":35123})
        assert r.status_code == 200 and "Los importes coinciden" in r.text
        assert "$35.123" in r.text
        assert r.headers["cache-control"] == "no-store"
        assert c.post("/revisar", data={"electricidad":"nan", "total_documento":0}).status_code == 422
        assert c.post("/api/conciliar", json={"lineas":[], "total_documento":0}).status_code == 422
        assert 'value="personalizada" selected' in c.get("/").text
