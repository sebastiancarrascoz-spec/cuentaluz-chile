"""Casos sintéticos del motor; no acreditan tarifas de una distribuidora."""
from decimal import Decimal
from pathlib import Path
import pytest
from pydantic import ValidationError
from app.services.tariff_engine import TariffProfile, SupplyContext, calcular_componentes


def perfil():
    return TariffProfile(id="caso_sintetico", empresa="PRUEBA", cut="13118", sector="S1", red="BT_AA",
        opcion="BT4.3", condicion="revisar", desde="2026-10-01", hasta="2026-10-31",
        fuente="https://example.org/fixture-no-oficial.pdf", cargos=[
            {"nombre":"Energía", "cantidad":"energia_kwh", "unidad":"$/kWh", "precio_neto":"100.125", "tratamiento":"afecto", "pagina_o_celda":"1"},
            {"nombre":"Demanda facturable", "cantidad":"demanda_facturable_kw", "unidad":"$/kW/mes", "precio_neto":"2000", "tratamiento":"afecto", "pagina_o_celda":"2"},
            {"nombre":"Exento", "cantidad":"energia_kwh", "unidad":"$/kWh", "precio_neto":"0.855", "tratamiento":"exento", "pagina_o_celda":"1"}])


def contexto(p):
    return SupplyContext(**{k:v for k,v in p.model_dump().items() if k in SupplyContext.model_fields})


def test_demanda_es_cantidad_independiente_y_no_inventada():
    p = perfil()
    with pytest.raises(ValueError, match="aprobación"):
        calcular_componentes(p, contexto(p), {"energia_kwh":100, "demanda_facturable_kw":5})
    with pytest.raises(ValueError, match="cantidades"):
        calcular_componentes(p, contexto(p), {"energia_kwh":100}, revision_interna=True)
    r = calcular_componentes(p, contexto(p), {"energia_kwh":100, "demanda_facturable_kw":5}, revision_interna=True)
    assert (r["neto_afecto"], r["iva"], r["exento"], r["total"]) == (20013, 3802, 86, 23901)


def test_no_usa_otro_sector_ni_extiende_vigencia():
    p = perfil()
    for cambio in ({"cut":"13101"}, {"red":"BT_SS"}, {"opcion":"BT1"}, {"hasta":"2026-11-01"}):
        c = SupplyContext(**{**contexto(p).model_dump(), **cambio})
        with pytest.raises(ValueError):
            calcular_componentes(p, c, {"energia_kwh":100, "demanda_facturable_kw":5}, revision_interna=True)


def test_aprobacion_no_es_solo_bandera():
    with pytest.raises(ValidationError, match="aprobación"):
        TariffProfile(**{**perfil().model_dump(), "estado":"aprobado"})
    with pytest.raises(ValueError, match="Cantidades"):
        p = perfil()
        calcular_componentes(p, contexto(p), {"energia_kwh":Decimal("NaN"), "demanda_facturable_kw":5}, revision_interna=True)


def test_candidato_enel_no_se_promueve_y_no_extiende_sus_condiciones():
    path = Path(__file__).resolve().parents[1] / "config/enel_macul_octubre_candidato.json"
    p = TariffProfile.model_validate_json(path.read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="aprobación"):
        calcular_componentes(p, contexto(p), {"energia_kwh":145, "mes_facturado":1})
    r = calcular_componentes(p, contexto(p), {"energia_kwh":145, "mes_facturado":1}, revision_interna=True)
    # El original del caso suma 35.123; se conserva la diferencia, sin ajustar el fijo.
    assert r["total"] == 35124
    with pytest.raises(ValueError, match="condiciones"):
        calcular_componentes(p, contexto(p), {"energia_kwh":351, "mes_facturado":1}, revision_interna=True)
