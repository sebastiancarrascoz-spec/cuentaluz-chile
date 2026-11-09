"""Casos sintéticos: memoria de demanda, faltantes y cambio de temporada."""
import pytest
from pydantic import ValidationError
from app.services.demand_service import DemandInput, evaluar_demanda


def caso(opcion="BT4.3", mes="2026-11"):
    from app.services.demand_service import month_index, month_name
    months = [month_name(i) for i in range(month_index(mes)-11, month_index(mes)+1)]
    # Calendario ficticio declarado para estos casos, no calendario oficial.
    rows = [{"mes":m, "contiene_horas_punta":4 <= int(m[-2:]) <= 9,
        "maxima_kw":50, "punta_kw":20 if 4 <= int(m[-2:]) <= 9 else None} for m in months]
    for r in rows:
        if r["mes"] == "2026-05":
            r.update(maxima_kw=120, punta_kw=80)
        if r["mes"] == "2026-08":
            r.update(maxima_kw=100, punta_kw=60)
    d = {"opcion":opcion, "mes_facturacion":mes, "historico":rows,
        "meses_punta_anterior": [r["mes"] for r in rows if r["contiene_horas_punta"]] if int(mes[-2:]) not in range(4,10) else []}
    if opcion.endswith("4.2"):
        d["potencia_contratada_kw"] = 150
    return d


@pytest.mark.parametrize("opcion", ["BT4.3", "AT4.3"])
def test_fuera_de_punta_no_usa_solo_el_mes_actual(opcion):
    r = evaluar_demanda(DemandInput(**caso(opcion)))
    assert r["cantidades"] == {"demanda_facturable_punta_kw":"70", "demanda_facturable_suministrada_kw":"110"}
    assert r["meses_origen_punta"] == ["2026-05", "2026-08"]
    assert r["meses_origen_suministrada"] == ["2026-05", "2026-08"]


def test_mes_con_punta_usa_su_lectura_y_conserva_memoria_suministrada():
    r = evaluar_demanda(DemandInput(**caso(mes="2026-09")))
    assert r["cantidades"]["demanda_facturable_punta_kw"] == "20"
    assert r["cantidades"]["demanda_facturable_suministrada_kw"] == "110"


@pytest.mark.parametrize("opcion", ["BT4.2", "AT4.2"])
def test_potencia_contratada_es_independiente_de_las_lecturas(opcion):
    r = evaluar_demanda(DemandInput(**caso(opcion)))
    assert r["cantidades"] == {"demanda_facturable_punta_kw":"70", "potencia_contratada_kw":"150"}


@pytest.mark.parametrize("cambio", ["faltante", "duplicado", "mes_futuro", "punta_ausente", "punta_mayor", "periodo_incompleto", "nan"])
def test_falla_si_no_hay_base_para_calculo(cambio):
    d = caso()
    if cambio == "faltante": d["historico"].pop()
    if cambio == "duplicado": d["historico"][0] = d["historico"][1]
    if cambio == "mes_futuro": d["historico"][0]["mes"] = "2027-01"
    if cambio == "punta_ausente": d["historico"][5]["punta_kw"] = None
    if cambio == "punta_mayor": d["historico"][5]["punta_kw"] = 500
    if cambio == "periodo_incompleto": d["meses_punta_anterior"].pop()
    if cambio == "nan": d["historico"][0]["maxima_kw"] = "NaN"
    with pytest.raises(ValidationError): DemandInput(**d)


def test_lectura_cero_es_valida_y_faltante_no_lo_es():
    d = caso(mes="2026-09")
    d["historico"][-1].update(maxima_kw=0, punta_kw=0)
    assert evaluar_demanda(DemandInput(**d))["cantidades"]["demanda_facturable_punta_kw"] == "0"


def test_flujo_http_y_conciliacion_sin_persistencia():
    from starlette.testclient import TestClient
    from main import app
    with TestClient(app) as c:
        d = caso()
        r = c.post("/api/evaluar-demanda", json=d)
        assert r.status_code == 200
        assert r.json()["cantidades"]["demanda_facturable_suministrada_kw"] == "110"
        assert r.headers["cache-control"] == "no-store"
        form = {"opcion":d["opcion"], "mes_facturacion":d["mes_facturacion"],
            "meses_punta_anterior": ",".join(d["meses_punta_anterior"])}
        for row in d["historico"]:
            form["max_" + row["mes"]] = str(row["maxima_kw"])
            if row["contiene_horas_punta"]:
                form["calendario_" + row["mes"]] = "on"
                form["punta_" + row["mes"]] = str(row["punta_kw"])
        r = c.post("/demanda", data=form)
        assert r.status_code == 200 and "110 kW" in r.text and "70 kW" in r.text
        assert r.headers["cache-control"] == "no-store"
        assert c.get("/demanda").status_code == 200
        assert c.post("/demanda", data={"mes_facturacion":"no-es-mes"}).status_code == 422
        d["historico"][0]["maxima_kw"] = "NaN"
        assert c.post("/api/evaluar-demanda", json=d).status_code == 422
