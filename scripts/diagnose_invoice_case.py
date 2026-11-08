"""Caso anonimizado y escenario diagnóstico; no aprueba el perfil candidato."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.services.tariff_engine import TariffProfile, SupplyContext, calcular_componentes
from app.services.invoice_service import InvoiceInput, conciliar
from app.services.estimate_service import EstimateInput, estimar
from app.services.period_service import PeriodInput, evaluar_periodos

p = TariffProfile.model_validate_json((ROOT / "config/enel_macul_octubre_candidato.json").read_text(encoding="utf-8"))
s = SupplyContext(**{k:v for k,v in p.model_dump().items() if k in SupplyContext.model_fields})
candidate = calcular_componentes(p, s, {"mes_facturado":1, "energia_kwh":145}, revision_interna=True)
actual = conciliar(InvoiceInput(lineas=[
    {"nombre":n, "neto":v, "tratamiento":t} for n,v,t in [
        ("Electricidad",26300,"afecto"), ("Administración",614,"afecto"),
        ("Transporte",2497,"afecto"), ("Servicio público",124,"exento")]], total_documento=35123))
legacy = estimar(EstimateInput(kwh=145, fuente="referencia"))
temporal_config = json.loads((ROOT / "config/enel_macul_temporal_diagnostico.json").read_text(encoding="utf-8"))
temporal = evaluar_periodos(PeriodInput(**temporal_config["entrada"]))
result = {"consumo_kwh":145, "catalogo_historico":legacy["total"], "conciliacion_importes":actual,
    "escenario_temporal":temporal, "supuestos_temporales":temporal_config["supuestos"],
    "diferencias_cargos_redondeados_temporales": {k:temporal["componentes_redondeados"][k] - v for k,v in
        {"electricidad":26300, "transporte":2497, "administracion":614, "exentos":124}.items()},
    "escenario_candidato_octubre":candidate,
    "diferencia_candidato_documento":candidate["total"] - actual["total"],
    "limitaciones":[
        "El candidato usa los precios publicados de octubre y confirma un valor compatible, pero no valida la factura.",
        "El período real abarca septiembre y octubre; falta revisar la aplicación temporal de ambos pliegos.",
        "No se deduce ETR T1 del consumo de 145 kWh del mes: exige promedio del año anterior.",
        "La red BT_AA y la equivalencia con la identificación del suministro deben confirmarse.",
        "El cargo fijo calculado al peso difiere del documento en $1; no se modifica el precio para forzar coincidencia.",
        "La lectura del PDF oficial se hizo mediante la consulta web; la descarga del original está bloqueada y no tiene SHA-256 local.",
        "El final de octubre es un límite conservador de este candidato, no una fecha de término declarada en el PDF."
    ]}
out = ROOT / "artifacts/boleta-revision/diagnostico_anonimizado.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"historico":legacy["total"], "documento_reconciliado":actual["total"],
    "temporal_por_cargo":temporal["alternativas"]["por_cargo"]["total"],
    "temporal_sobre_subtotal":temporal["alternativas"]["sobre_subtotal"]["total"],
    "candidato_octubre":candidate["total"], "diferencia":result["diferencia_candidato_documento"], "estado":"pendiente"}))
