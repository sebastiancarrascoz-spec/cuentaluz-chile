"""Cargo de demanda BT3/AT3 con datos declarados: 5T/2024, 4.5 y 4.10.

La memoria en kW usa los máximos mensuales de meses que contienen punta,
no las lecturas máximas restringidas a horas de punta. El mínimo histórico
es monetario y conserva la base neta de los cargos anteriores.
"""
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.services.demand_service import SOURCE, month_index, month_name
from app.services.period_service import round_peso


def importe_exacto(value):
    with localcontext() as ctx:
        ctx.prec = 60
        return format(Decimal(value.numerator) / Decimal(value.denominator), "f")


class Demand3Month(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    mes: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    contiene_horas_punta: bool
    maxima_kw: Decimal | None = Field(default=None, ge=0, le=1000000000, decimal_places=6)
    cargo_demanda_neto: Decimal | None = Field(default=None, ge=0, le=1000000000000, decimal_places=4)

    @model_validator(mode="after")
    def fecha(self):
        month_index(self.mes)
        return self


class Demand3Input(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    opcion: Literal["BT3", "AT3"]
    mes_facturacion: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    clasificacion: Literal["presente_en_punta", "parcialmente_presente_en_punta"]
    precio_demanda_neto: Decimal = Field(ge=0, le=1000000000, decimal_places=6)
    historico: list[Demand3Month] = Field(min_length=13, max_length=13)
    ventana_minimo_confirmada: Literal["doce_previos", "incluye_mes_facturado"] | None = None
    cargo_observado_neto: int | None = Field(default=None, ge=0, le=1000000000000)

    @model_validator(mode="after")
    def historial_completo(self):
        last = month_index(self.mes_facturacion)
        expected = {month_name(i) for i in range(last - 12, last + 1)}
        if {m.mes for m in self.historico} != expected:
            raise ValueError("Se requieren 13 meses consecutivos: doce antecedentes y el mes facturado, sin duplicados.")
        for m in self.historico:
            if m.mes == self.mes_facturacion and m.cargo_demanda_neto is not None:
                raise ValueError("El cargo actual se compara aparte; no se usa como antecedente de sí mismo.")
            if m.mes != self.mes_facturacion and m.cargo_demanda_neto is None:
                raise ValueError("Falta un cargo neto anterior; un faltante no equivale a cero.")
            if m.mes != month_name(last - 12) and m.maxima_kw is None:
                raise ValueError("Falta un máximo mensual dentro de los doce meses de demanda.")
        if sum(m.contiene_horas_punta for m in self.historico if m.mes != month_name(last - 12)) < 2:
            raise ValueError("Esta evaluación requiere al menos dos meses con punta en el histórico declarado.")
        return self


def evaluar_demanda3(entrada: Demand3Input):
    rows = sorted(entrada.historico, key=lambda m: m.mes)
    actual = rows[-1]
    peaks = sorted((m for m in rows[1:] if m.contiene_horas_punta), key=lambda m: (-m.maxima_kw, m.mes))[:2]
    memory = sum((m.maxima_kw for m in peaks), Decimal(0)) / 2
    demand = max(actual.maxima_kw, memory)
    base = Fraction(demand) * Fraction(entrada.precio_demanda_neto)
    alternatives = {}
    for key, history in [("doce_previos",rows[:-1]), ("incluye_mes_facturado",rows[1:-1])]:
        biggest = sorted(history, key=lambda m: (-m.cargo_demanda_neto, m.mes))[0]
        floor = Fraction(biggest.cargo_demanda_neto) * Fraction(2,5)
        chosen = max(base, floor)
        # Si la ventana incluye el cargo actual C, C=max(B,0.4*max(H,C)).
        # Para B,H no negativos, la solución es max(B,0.4*H). Se muestra
        # además el mínimo resultante al volver a incluir ese cargo C.
        effective_floor = Fraction(2,5) * max(Fraction(biggest.cargo_demanda_neto), chosen) if key == "incluye_mes_facturado" else floor
        alternatives[key] = {"maximo_cargo_historico_neto":str(biggest.cargo_demanda_neto),
            "mes_maximo_cargo_historico":biggest.mes, "minimo_sobre_antecedentes_neto":importe_exacto(floor),
            "minimo_resultante_neto":importe_exacto(effective_floor), "aplica_minimo_historico":floor > base,
            "ajuste_por_minimo_neto_sin_redondear":importe_exacto(chosen-base),
            "cargo_demanda_neto_sin_redondear":importe_exacto(chosen), "cargo_demanda_neto":round_peso(chosen)}
    equal = alternatives["doce_previos"]["cargo_demanda_neto_sin_redondear"] == alternatives["incluye_mes_facturado"]["cargo_demanda_neto_sin_redondear"]
    selected = entrada.ventana_minimo_confirmada
    resolved = alternatives[selected] if selected else alternatives["doce_previos"] if equal else None
    charge = resolved["cargo_demanda_neto"] if resolved else None
    return {"opcion":entrada.opcion, "mes_facturacion":entrada.mes_facturacion,
        "clasificacion_declarada":entrada.clasificacion,
        "demanda_actual_kw":str(actual.maxima_kw), "promedio_maximos_meses_punta_kw":str(memory),
        "demanda_facturable_base_kw":str(demand), "meses_origen_memoria_kw":[m.mes for m in peaks],
        "origen_demanda_base":"mes_actual" if actual.maxima_kw >= memory else "memoria_meses_con_punta",
        "precio_demanda_neto":str(entrada.precio_demanda_neto), "cargo_base_neto_sin_redondear":importe_exacto(base),
        "ventana_minimo_confirmada":selected, "alternativas":alternatives,
        "ventanas_producen_mismo_cargo":equal, "resultado":resolved, "cargo_demanda_neto":charge,
        "cargo_observado_neto":entrada.cargo_observado_neto,
        "diferencia_observado_menos_calculo":entrada.cargo_observado_neto - charge if entrada.cargo_observado_neto is not None and charge is not None else None,
        "estado":"evaluacion_con_datos_y_precio_declarados", "fuente":SOURCE,
        "referencia":"Decreto 5T/2024, numerales 4.5, 4.10 y 5.4, páginas 14 a 19.",
        "alcance":"Solo cargo de demanda neto, sin IVA ni otros cargos: no es el total de la cuenta. Calendario, clasificación, precio y ventana del mínimo requieren verificación. Si las ventanas difieren y no se confirma una, no se entrega un cargo único. La coincidencia de alternativas no aprueba la ventana. El piso monetario no se convierte en kW medidos. No cubre históricos incompletos, cambios de opción o condiciones especiales."}
