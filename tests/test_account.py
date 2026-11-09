from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from main import app
from app.services.account_service import AccountInput, evaluar_cuenta, CATEGORIES
from tests.test_demand3 import caso as demanda3


def case():
    return {"periodo":{"lectura_anterior":"2026-10-31", "lectura_actual":"2026-11-30", "kwh":"100",
        "precios":[{"desde":"2026-11-01", "hasta":"2026-11-30", "electricidad_neta":"100",
            "transporte_neto":"10", "servicio_exento":"1", "fijo_neto":"500"}],
        "asignacion":"dias", "modo_fijo":"ponderado", "redondeo":"por_cargo"},
        "respaldo_precios":"Caso ficticio; precios sin validez comercial.",
        "adicionales":{k:{"estado":"no_aplica","respaldo":"Excluido en este caso ficticio."} for k in CATEGORIES}}


def test_complete_bill_tax_once_and_signed_final_credit():
    d = case()
    d["adicionales"]["demanda"] = {"estado":"declarado","importe":"2000","respaldo":"Ficticio"}
    d["adicionales"]["reactiva"] = {"estado":"declarado","importe":"300","respaldo":"Ficticio"}
    d["adicionales"]["otros_exentos"] = {"estado":"declarado","importe":"50","respaldo":"Ficticio"}
    d["adicionales"]["ajustes_finales"] = {"estado":"declarado","importe":"-1000","respaldo":"Saldo ficticio"}
    d["total_documento"] = 15572
    r = evaluar_cuenta(AccountInput(**d))
    # 10000 + 1000 + 500 + 2000 + 300 = 13800; IVA 2622.
    assert (r["neto_afecto"],r["iva"],r["exentos"],r["total"]) == (13800,2622,150,15572)
    assert r["diferencia"] == 0 and not r["tarifa_oficial_validada"]
    assert len([c for c in r["componentes"] if c["id"] == "administracion"]) == 1


def test_consolidates_bt3_monetary_minimum_not_kw_times_price():
    d=case(); d["demanda3"] = demanda3()
    d["adicionales"]["demanda"]["estado"]="calculada"
    r=evaluar_cuenta(AccountInput(**d))
    assert r["neto_afecto"] == 171500  # 11500 + piso monetario 160000
    assert r["iva"] == 32585 and r["total"] == 204185


def test_ambiguous_bt3_refuses_full_total():
    d=case(); d["demanda3"] = demanda3()
    d["adicionales"]["demanda"]["estado"]="calculada"
    d["demanda3"]["historico"][0]["cargo_demanda_neto"]="1000000"
    with pytest.raises(ValueError,match="importe único"):
        evaluar_cuenta(AccountInput(**d))
    response=TestClient(app).post('/api/evaluar-cuenta', json=d)
    assert response.status_code==422


def test_demand4_prices_both_quantities_separately():
    from tests.test_demand import caso
    d=case()
    d["demanda4"]={"datos":caso(), "precio_punta_neto":"1000", "precio_suministrada_o_contratada_neto":"2000", "respaldo":"Ficticio"}
    d["adicionales"]["demanda"]["estado"]="calculada"
    r=evaluar_cuenta(AccountInput(**d))
    q=r["demanda"]["cantidades"]
    expected=int(q["demanda_facturable_punta_kw"])*1000+int(q["demanda_facturable_suministrada_kw"])*2000+11500
    assert r["neto_afecto"]==expected


@pytest.mark.parametrize("change",["missing", "extra", "null", "not_applicable_with_amount", "empty_declared", "negative_taxable", "fractional_final", "wrong_month", "duplicate_demand"])
def test_rejects_missing_and_contradictory_inputs(change):
    d=case()
    if change=="missing": d["adicionales"].pop("reactiva")
    if change=="extra": d["adicionales"]["otro"] = deepcopy(d["adicionales"]["reactiva"])
    if change=="null": d["adicionales"]["reactiva"] = None
    if change=="not_applicable_with_amount": d["adicionales"]["reactiva"]["importe"]="0"
    if change=="empty_declared": d["adicionales"]["reactiva"]["estado"]="declarado"
    if change=="negative_taxable": d["adicionales"]["reactiva"].update(estado="declarado",importe="-1")
    if change=="fractional_final": d["adicionales"]["ajustes_finales"].update(estado="declarado",importe="0.5")
    if change=="wrong_month":
        d["demanda3"]=demanda3()
        d["adicionales"]["demanda"]["estado"]="calculada"
        d["periodo"].update(lectura_anterior="2026-09-30",lectura_actual="2026-10-31")
        d["periodo"]["precios"][0].update(desde="2026-10-01",hasta="2026-10-31")
    if change=="duplicate_demand":
        d["demanda3"]=demanda3()
        d["adicionales"]["demanda"].update(estado="declarado",importe="1")
    with pytest.raises(ValidationError): AccountInput(**d)


def test_exact_fraction_survives_display_precision_and_exempt_rounding_is_visible():
    d=case(); p=d["periodo"]; p["kwh"]="0.0001"
    p["redondeo"]="sobre_subtotal"
    p["precios"][0].update(electricidad_neta="4999.999999",transporte_neto="0",fijo_neto="0",servicio_exento="5000")
    d["adicionales"]["otros_exentos"].update(estado="declarado",importe="0.5")
    r=evaluar_cuenta(AccountInput(**d))
    assert r["neto_afecto"]==0  # Producto 0,4999999999, no el texto mostrado 0,500000.
    assert r["exentos"]==1 and r["ajuste_redondeo_exento"]==-1


def test_api_and_form_preserve_no_store_and_no_official_claim():
    client=TestClient(app)
    r=client.post('/api/evaluar-cuenta',json=case())
    assert r.status_code==200 and r.headers["cache-control"]=="no-store"
    assert r.json()["total"]==13785
    form={"lectura_anterior":"2026-10-31","lectura_actual":"2026-11-30","kwh":"100",
        "electricidad_neta_1":"100","transporte_neto_1":"10","servicio_exento_1":"1","fijo_neto_1":"500",
        "asignacion":"dias","modo_fijo":"ponderado","redondeo":"por_cargo","respaldo_precios":"Ficticio"}
    for k in CATEGORIES: form.update({k+"_estado":"no_aplica",k+"_respaldo":"Excluido en el caso"})
    r=client.post('/cuenta',data=form)
    assert r.status_code==200 and "$13.785" in r.text
    form["fijo_neto_2"]="1"
    assert client.post('/cuenta',data=form).status_code==422


def test_transfer_keeps_historical_minimum_and_revalidates_tampering():
    import json
    client=TestClient(app)
    transfer={"tipo_demanda":"3","datos_demanda":json.dumps(demanda3())}
    r=client.post('/cuenta/preparar-demanda',data=transfer)
    assert r.status_code==200 and r.headers['cache-control']=='no-store'
    assert '$160.000' in r.text and '2026-05' in r.text
    form={**transfer,"lectura_anterior":"2026-10-31","lectura_actual":"2026-11-30","kwh":"100",
        "electricidad_neta_1":"100","transporte_neto_1":"10","servicio_exento_1":"1","fijo_neto_1":"500",
        "modo_fijo":"ponderado","redondeo":"por_cargo","respaldo_precios":"Ficticio"}
    for k in CATEGORIES: form.update({k+'_estado':'calculada' if k=='demanda' else 'no_aplica',k+'_respaldo':'Datos ficticios'})
    r=client.post('/cuenta',data=form)
    assert r.status_code==200 and '$204.185' in r.text
    form['demanda_importe']='160000'
    assert client.post('/cuenta',data=form).status_code==422  # No duplicar el cargo transferido.
    corrupted=demanda3(); corrupted['historico'][0]['cargo_demanda_neto']='1000000'
    transfer['datos_demanda']=json.dumps(corrupted)
    assert client.post('/cuenta/preparar-demanda',data=transfer).status_code==422


def test_manual_category_requires_real_text_and_calculated_requires_histories():
    d=case(); d['respaldo_precios']='   '
    with pytest.raises(ValidationError): AccountInput(**d)
    d=case(); d['adicionales']['demanda']['estado']='calculada'
    with pytest.raises(ValidationError): AccountInput(**d)
    d=case(); d['adicionales']['reactiva']['estado']='calculada'
    with pytest.raises(ValidationError): AccountInput(**d)
