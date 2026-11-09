import pytest
from pydantic import ValidationError
from app.services.demand3_service import Demand3Input, evaluar_demanda3


def caso(opcion="BT3"):
    months = ["2025-11", "2025-12"] + [f"2026-{i:02d}" for i in range(1,12)]
    rows = [{"mes":m, "contiene_horas_punta":4 <= int(m[-2:]) <= 9, "maxima_kw":"50",
        "cargo_demanda_neto":"50000" if m != "2026-11" else None} for m in months]
    for r in rows:
        if r["mes"] == "2026-05": r.update(maxima_kw="120", cargo_demanda_neto="400000")
        if r["mes"] == "2026-08": r.update(maxima_kw="100", cargo_demanda_neto="100000")
    return {"opcion":opcion, "mes_facturacion":"2026-11", "clasificacion":"presente_en_punta",
        "precio_demanda_neto":"1000", "historico":rows}


@pytest.mark.parametrize("opcion", ["BT3", "AT3"])
def test_piso_es_monetario_y_no_el_cuarenta_por_ciento_de_kw(opcion):
    r = evaluar_demanda3(Demand3Input(**caso(opcion)))
    assert r["demanda_facturable_base_kw"] == "110"
    assert r["cargo_base_neto_sin_redondear"] == "110000"
    assert r["cargo_demanda_neto"] == 160000
    assert r["resultado"]["aplica_minimo_historico"]
    assert r["resultado"]["ajuste_por_minimo_neto_sin_redondear"] == "50000"
    assert r["meses_origen_memoria_kw"] == ["2026-05", "2026-08"]


def test_mes_actual_supera_memoria_y_piso():
    d = caso()
    d["historico"][-1]["maxima_kw"] = "200"
    r = evaluar_demanda3(Demand3Input(**d))
    assert r["cargo_demanda_neto"] == 200000 and not r["resultado"]["aplica_minimo_historico"]
    assert r["origen_demanda_base"] == "mes_actual"


def test_memoria_usa_maximo_mensual_incluso_fuera_de_horas_punta():
    d = caso()
    d["historico"][5]["punta_kw"] = 1
    with pytest.raises(ValidationError): Demand3Input(**d)


def test_precio_cero_conserva_piso_en_dinero():
    d = caso()
    d["precio_demanda_neto"] = "0"
    assert evaluar_demanda3(Demand3Input(**d))["cargo_demanda_neto"] == 160000


@pytest.mark.parametrize("cambio", ["falta_cargo", "duplicado", "mes_futuro", "cargo_actual", "sin_punta", "nan", "negativo", "clasificacion"])
def test_rechaza_base_incompleta_o_incoherente(cambio):
    d = caso()
    if cambio == "falta_cargo": d["historico"][0]["cargo_demanda_neto"] = None
    if cambio == "duplicado": d["historico"][0]["mes"] = d["historico"][1]["mes"]
    if cambio == "mes_futuro": d["historico"][0]["mes"] = "2027-01"
    if cambio == "cargo_actual": d["historico"][-1]["cargo_demanda_neto"] = 1
    if cambio == "sin_punta":
        for r in d["historico"]: r["contiene_horas_punta"] = False
    if cambio == "nan": d["precio_demanda_neto"] = "NaN"
    if cambio == "negativo": d["historico"][0]["cargo_demanda_neto"] = -1
    if cambio == "clasificacion": d.pop("clasificacion")
    with pytest.raises(ValidationError): Demand3Input(**d)


def test_comparacion_no_alimenta_el_minimo_y_redondeo_no_es_bancario():
    d = caso()
    d["cargo_observado_neto"] = 1
    r = evaluar_demanda3(Demand3Input(**d))
    assert r["cargo_demanda_neto"] == 160000
    assert r["diferencia_observado_menos_calculo"] == -159999
    for row in d["historico"]:
        row["maxima_kw"] = "1"
        if row["mes"] != "2026-11": row["cargo_demanda_neto"] = "0"
    d["precio_demanda_neto"] = "2.5"
    assert evaluar_demanda3(Demand3Input(**d))["cargo_demanda_neto"] == 3


def test_ventana_no_confirmada_no_oculta_diferencia_por_mes_mas_antiguo():
    d = caso()
    d["historico"][0]["cargo_demanda_neto"] = "1000000"
    r = evaluar_demanda3(Demand3Input(**d))
    assert r["cargo_demanda_neto"] is None
    assert r["alternativas"]["doce_previos"]["cargo_demanda_neto"] == 400000
    assert r["alternativas"]["incluye_mes_facturado"]["cargo_demanda_neto"] == 160000
    d["ventana_minimo_confirmada"] = "doce_previos"
    assert evaluar_demanda3(Demand3Input(**d))["cargo_demanda_neto"] == 400000


def test_limite_alto_no_redondea_hacia_arriba_antes_del_peso_final():
    d = caso()
    for row in d["historico"]:
        row["maxima_kw"] = "0"
        if row["mes"] != "2026-11": row["cargo_demanda_neto"] = "0"
        if row["mes"] == "2026-05": row["maxima_kw"] = "999500000.000000"
        if row["mes"] == "2026-08": row["maxima_kw"] = "999500000.000001"
    d["precio_demanda_neto"] = "999999999.999999"
    r = evaluar_demanda3(Demand3Input(**d))
    assert r["cargo_base_neto_sin_redondear"] == "999499999999999500.4999999999995"
    assert r["cargo_demanda_neto"] == 999499999999999500


def test_flujo_html_api_y_ventana_pendiente():
    from starlette.testclient import TestClient
    from main import app
    with TestClient(app) as c:
        d = caso()
        assert c.get("/demanda-3").status_code == 200
        r = c.post("/api/evaluar-demanda-3", json=d)
        assert r.status_code == 200 and r.json()["cargo_demanda_neto"] == 160000
        assert r.headers["cache-control"] == "no-store"
        form = {k:d[k] for k in ("opcion","mes_facturacion","clasificacion","precio_demanda_neto")}
        for row in d["historico"]:
            form["max_" + row["mes"]] = row["maxima_kw"]
            if row["contiene_horas_punta"]: form["calendario_" + row["mes"]] = "on"
            if row["cargo_demanda_neto"] is not None: form["cargo_" + row["mes"]] = row["cargo_demanda_neto"]
        r = c.post("/demanda-3", data=form)
        assert r.status_code == 200 and "$160.000" in r.text
        form["cargo_2025-11"] = "1000000"
        r = c.post("/demanda-3", data=form)
        assert r.status_code == 200 and "La ventana del mínimo cambia el resultado" in r.text
        assert "Cargo de demanda neto:" not in r.text
        assert c.post("/demanda-3", data={"mes_facturacion":"no-es-mes"}).status_code == 422
