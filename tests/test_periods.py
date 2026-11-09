from decimal import Decimal
from fractions import Fraction
import pytest
from pydantic import ValidationError
from app.services.period_service import PeriodInput, evaluar_periodos, round_peso


def caso():
    return {"lectura_anterior":"2026-09-23", "lectura_actual":"2026-10-21", "kwh":"145",
        "asignacion":"dias", "modo_fijo":"ponderado", "redondeo":"por_cargo", "precios":[
            {"desde":"2026-09-01","hasta":"2026-09-30", "electricidad_neta":"181.407", "transporte_neto":"17.218", "servicio_exento":"0.855", "fijo_neto":"611.118"},
            {"desde":"2026-10-01","hasta":"2026-10-31", "electricidad_neta":"181.376", "transporte_neto":"17.218", "servicio_exento":"0.855", "fijo_neto":"614.924"}]}


def test_intervalo_entre_lecturas_y_conservacion_exacta():
    r = evaluar_periodos(PeriodInput(**caso()))
    assert r["dias"] == 28
    assert [i["dias"] for i in r["intervalos"]] == [7,21]
    assert sum((Fraction(i["kwh_fraccion"]) for i in r["intervalos"]), Fraction(0)) == 145
    assert [i["kwh"] for i in r["intervalos"]] == ["36.250000","108.750000"]
    assert r["componentes_sin_redondear"]["administracion"] == "613.972500"
    assert r["alternativas"]["por_cargo"]["total"] == 35124
    assert r["alternativas"]["sobre_subtotal"]["total"] == 35123
    assert r["alternativas"]["sobre_subtotal"]["ajuste_redondeo"] == -1


@pytest.mark.parametrize("cambio", ["hueco", "superposicion", "invertido", "cero_dias", "faltan_precios", "nan", "negativo"])
def test_no_inventa_precios_ni_oculta_intervalos_invalidos(cambio):
    d = caso()
    if cambio == "hueco": d["precios"][1]["desde"] = "2026-10-02"
    if cambio == "superposicion": d["precios"][1]["desde"] = "2026-09-30"
    if cambio == "invertido": d["precios"][0]["hasta"] = "2026-08-31"
    if cambio == "cero_dias": d["lectura_actual"] = d["lectura_anterior"]
    if cambio == "faltan_precios": d["precios"].pop()
    if cambio == "nan": d["kwh"] = "NaN"
    if cambio == "negativo": d["precios"][0]["fijo_neto"] = -1
    with pytest.raises(ValidationError): PeriodInput(**d)


def test_lecturas_reales_sustituyen_reparto_y_deben_sumar_total():
    d = caso()
    d["asignacion"] = "lecturas"
    d["precios"][0]["kwh_medido"] = "40"
    d["precios"][1]["kwh_medido"] = "105"
    r = evaluar_periodos(PeriodInput(**d))
    assert r["intervalos"][0]["kwh"] == "40.000000"
    d["precios"][1]["kwh_medido"] = "104"
    with pytest.raises(ValidationError, match="no suman"): PeriodInput(**d)


def test_fijo_declarado_se_cobra_una_sola_vez():
    d = caso()
    d.update(modo_fijo="declarado", fijo_neto_periodo="614")
    for p in d["precios"]:
        p.pop("fijo_neto")
    assert evaluar_periodos(PeriodInput(**d))["componentes_redondeados"]["administracion"] == 614


def test_bisiesto_y_fracciones_periodicas_no_pierden_energia():
    d = caso()
    d.update(lectura_anterior="2024-02-27", lectura_actual="2024-03-01", kwh="1")
    d["precios"][0].update(desde="2024-02-01", hasta="2024-02-29")
    d["precios"][1].update(desde="2024-03-01", hasta="2024-03-31")
    r = evaluar_periodos(PeriodInput(**d))
    assert r["dias"] == 3
    assert [i["kwh_fraccion"] for i in r["intervalos"]] == ["2/3","1/3"]
    assert round_peso(Fraction(5,2)) == 3
    assert round_peso(Fraction(-5,2)) == -3


def test_cero_real_y_limite_superior_del_calendario():
    d = caso()
    d["kwh"] = 0
    r = evaluar_periodos(PeriodInput(**d))
    assert r["componentes_redondeados"]["electricidad"] == 0
    assert r["componentes_redondeados"]["administracion"] == 614
    d.update(lectura_anterior="9999-12-30", lectura_actual="9999-12-31")
    with pytest.raises(ValidationError): PeriodInput(**d)


def test_http_y_error_sin_precios_faltantes_silenciosos():
    from starlette.testclient import TestClient
    from main import app
    with TestClient(app) as c:
        d = caso()
        r = c.post("/api/evaluar-periodos", json=d)
        assert r.status_code == 200 and r.json()["total"] == 35124
        assert r.headers["cache-control"] == "no-store"
        assert c.get("/periodos").status_code == 200
        data = {k:d[k] for k in ("lectura_anterior", "lectura_actual", "kwh", "modo_fijo", "redondeo")}
        data["cambio"] = "2026-10-01"
        for i, p in enumerate(d["precios"], 1):
            for key in ("electricidad_neta", "transporte_neto", "servicio_exento", "fijo_neto"):
                data[f"{key}_{i}"] = p[key]
        r = c.post("/periodos", data=data)
        assert r.status_code == 200 and "$35.124" in r.text and "$35.123" in r.text
        assert c.post("/periodos", data={**data, "cambio":"2026-10-22"}).status_code == 422
        d["precios"].pop()
        assert c.post("/api/evaluar-periodos", json=d).status_code == 422


def test_dividir_un_mismo_precio_no_duplica_fijo_ni_cambia_la_factura():
    d = caso()
    for p in d["precios"]:
        for key in ("electricidad_neta", "transporte_neto", "servicio_exento", "fijo_neto"):
            p[key] = d["precios"][1][key]
    dividido = evaluar_periodos(PeriodInput(**d))
    d["precios"] = [{**d["precios"][1], "desde":"2026-09-24", "hasta":"2026-10-21"}]
    unico = evaluar_periodos(PeriodInput(**d))
    assert dividido["componentes_sin_redondear"] == unico["componentes_sin_redondear"]
    assert dividido["alternativas"] == unico["alternativas"]
