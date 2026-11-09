"""Contraste de importes observados; ninguna coincidencia acredita precios."""
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

Pesos = Annotated[int, Field(strict=True, ge=0, le=1000000000000000)]
SignedPesos = Annotated[int, Field(strict=True, ge=-1000000000000, le=1000000000000)]


class ObservedAmounts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    electricidad: Pesos | None = None
    transporte: Pesos | None = None
    administracion: Pesos | None = None
    demanda: Pesos | None = None
    reactiva: Pesos | None = None
    otros_afectos: Pesos | None = None
    exentos: Pesos | None = None
    ajustes_finales: SignedPesos | None = None
    neto_afecto: Pesos | None = None
    iva: Pesos | None = None
    total: Pesos | None = None


LABELS = {"electricidad":"Electricidad consumida", "transporte":"Transporte", "administracion":"Administración",
    "demanda":"Potencia y demanda", "reactiva":"Reactiva y recargos", "otros_afectos":"Otros afectos",
    "exentos":"Total exento", "ajustes_finales":"Ajustes finales", "neto_afecto":"Neto afecto", "iva":"IVA 19 %", "total":"Total"}
GUIDANCE = {"electricidad":"Revisa precios por vigencia, reparto del consumo, tramo ETR y componentes incluidos. No sumes distribución dos veces.",
    "administracion":"Revisa el período y la aplicación del fijo; una cuenta con dos precios no exige dos cargos fijos completos.",
    "transporte":"Revisa vigencias y desglose. Algunos agregados incluyen servicio público exento; no lo dupliques ni le añadas IVA.",
    "demanda":"Revisa contrato, máximos históricos, calendario, clasificación y mínimo monetario. No derives demanda desde kWh.",
    "reactiva":"Confirma medición y regla de recargo aplicable.", "otros_afectos":"Identifica cada concepto y su base imponible.",
    "exentos":"Comprueba servicio público, recargos y exenciones; no asumas que todos los suministros usan el mismo tramo.",
    "ajustes_finales":"Distingue saldos y ajustes posteriores al IVA de descuentos que modifican la base imponible.",
    "neto_afecto":"Comprueba suma de cargos y política de redondeo.", "iva":"Contrasta base afecta e impuesto redondeado; no calcules IVA de nuevo sobre precios finales.",
    "total":"Revisa las diferencias por componente antes de atribuir una causa al total."}


def compare_observed(result, observed: ObservedAmounts):
    actual={k:0 for k in ("electricidad","transporte","administracion","demanda","reactiva","otros_afectos")}
    for row in result["componentes"]:
        key="demanda" if row["id"] in ("demanda","demanda_base","demanda_punta") else row["id"]
        if key in actual: actual[key]+=row["neto"]
    actual.update({k:result[k] for k in ("exentos","ajustes_finales","neto_afecto","iva","total")})
    supplied=observed.model_dump(exclude_none=True)
    rows=[]
    for key,label in LABELS.items():
        value=supplied.get(key)
        delta=value-actual[key] if value is not None else None
        rows.append({"id":key,"nombre":label,"calculado":actual[key],"observado":value,"diferencia":delta,
            "estado":"sin_antecedente" if value is None else "coincide" if delta==0 else "difiere",
            "revisar":GUIDANCE[key] if delta not in (None,0) else None,
            "diferencia_de_un_peso":abs(delta)==1 if delta is not None else False})
    warnings=[]
    if all(k in supplied for k in ("neto_afecto","iva","exentos","ajustes_finales","total")):
        if supplied["neto_afecto"]+supplied["iva"]+supplied["exentos"]+supplied["ajustes_finales"]!=supplied["total"]:
            warnings.append("Los resúmenes observados no reconstruyen el total del documento; revisa la transcripción.")
    affect_keys=("electricidad","transporte","administracion","demanda","reactiva","otros_afectos")
    observed_adjust=None
    if all(k in supplied for k in (*affect_keys,"neto_afecto")):
        observed_adjust=supplied["neto_afecto"]-sum(supplied[k] for k in affect_keys)
    changed=[r["id"] for r in rows if r["estado"]=="difiere"]
    matches_total=supplied.get("total")==result["total"] if "total" in supplied else None
    return {"filas":rows,"cargos_con_diferencia":changed,"total_coincide":matches_total,
        "total_coincide_con_cargos_distintos":matches_total is True and any(k not in ("neto_afecto","iva","total") for k in changed),
        "ajuste_observado_entre_cargos_y_neto":observed_adjust,"ajuste_calculado_entre_cargos_y_neto":result["ajuste_redondeo_afecto"],
        "avisos":warnings,"campos_sin_antecedente":[k for k in LABELS if k not in supplied],
        "alcance":"Diferencias documento menos escenario, en pesos. Un campo vacío no es cero. Las causas propuestas son verificaciones pendientes, no diagnósticos de cobro incorrecto. Un peso de diferencia no se asigna automáticamente al redondeo. Coincidir en total no valida los cargos ni la tarifa."}
