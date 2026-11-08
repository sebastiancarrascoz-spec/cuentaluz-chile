"""Cantidades de demanda BT/AT 4.2 y 4.3, según 5T/2024, 4.7-4.10.

La evaluación usa históricos y calendario declarados. No aprueba el calendario,
contrato, lecturas ni precios y no genera una cotización monetaria.
"""
from datetime import date
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

SOURCE = "https://www.cne.cl/wp-content/uploads/2025/08/Decreto-5T-2024-Toma-de-razon-1.pdf"


def month_index(value):
    year, month = map(int, value.split("-"))
    date(year, month, 1)
    return year * 12 + month - 1


def month_name(index):
    year, month = divmod(index, 12)
    return f"{year:04d}-{month + 1:02d}"


class DemandMonth(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    mes: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    contiene_horas_punta: bool
    maxima_kw: Decimal = Field(ge=0, le=1000000000, decimal_places=6)
    punta_kw: Decimal | None = Field(default=None, ge=0, le=1000000000, decimal_places=6)

    @model_validator(mode="after")
    def lectura_coherente(self):
        month_index(self.mes)
        if self.contiene_horas_punta and self.punta_kw is None:
            raise ValueError("Falta la lectura de punta; un dato faltante no equivale a cero.")
        if not self.contiene_horas_punta and self.punta_kw is not None:
            raise ValueError("El mes sin horas de punta no admite una lectura de punta.")
        if self.punta_kw is not None and self.punta_kw > self.maxima_kw:
            raise ValueError("La demanda en punta no puede superar el máximo del mismo mes.")
        return self


class DemandInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    opcion: Literal["BT4.2", "BT4.3", "AT4.2", "AT4.3"]
    mes_facturacion: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    historico: list[DemandMonth] = Field(min_length=12, max_length=12)
    potencia_contratada_kw: Decimal | None = Field(default=None, ge=0, le=1000000000, decimal_places=6)
    meses_punta_anterior: list[str] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def cobertura_historica(self):
        last = month_index(self.mes_facturacion)
        expected = {month_name(i) for i in range(last - 11, last + 1)}
        if {m.mes for m in self.historico} != expected:
            raise ValueError("Se requieren los 12 meses consecutivos, incluido el mes facturado, sin duplicados.")
        if self.opcion.endswith("4.2") and self.potencia_contratada_kw is None:
            raise ValueError("La opción 4.2 requiere potencia contratada.")
        if self.opcion.endswith("4.3") and self.potencia_contratada_kw is not None:
            raise ValueError("La opción 4.3 usa demanda suministrada; no se sustituye por potencia contratada.")
        rows = sorted(self.historico, key=lambda m: m.mes)
        if rows[-1].contiene_horas_punta:
            if self.meses_punta_anterior:
                raise ValueError("En un mes con punta se usa su lectura, sin declarar un período anterior.")
        else:
            chosen = self.meses_punta_anterior
            if len(set(chosen)) != len(chosen) or len(chosen) < 2:
                raise ValueError("Declara el período de punta anterior completo, con al menos dos meses distintos.")
            by_month = {m.mes: m for m in rows}
            if any(m not in by_month or m == self.mes_facturacion or not by_month[m].contiene_horas_punta for m in chosen):
                raise ValueError("El período anterior debe usar meses con punta presentes en el histórico.")
            # El período declarado debe coincidir con el último bloque completo
            # de meses con punta en el calendario informado, sin saltar meses.
            end = next((i for i in range(10, -1, -1) if rows[i].contiene_horas_punta), None)
            if end is None:
                raise ValueError("No hay un período de punta anterior en los registros.")
            start = end
            while start > 0 and rows[start - 1].contiene_horas_punta:
                start -= 1
            if set(chosen) != {m.mes for m in rows[start:end + 1]}:
                raise ValueError("El período declarado no coincide con el último período de punta informado completo.")
        return self


def evaluar_demanda(entrada: DemandInput):
    rows = sorted(entrada.historico, key=lambda m: m.mes)
    actual = rows[-1]
    if actual.contiene_horas_punta:
        punta = actual.punta_kw
        origin = [actual.mes]
        method = "Lectura en horas de punta del mes informado."
    else:
        season = [m for m in rows if m.mes in entrada.meses_punta_anterior]
        top = sorted(season, key=lambda m: (-m.punta_kw, m.mes))[:2]
        punta = sum((m.punta_kw for m in top), Decimal(0)) / 2
        origin = [m.mes for m in top]
        method = "Promedio de las dos mayores demandas en punta del período anterior declarado."
    quantities = {"demanda_facturable_punta_kw": str(punta)}
    supplied_origin = []
    if entrada.opcion.endswith("4.3"):
        top = sorted(rows, key=lambda m: (-m.maxima_kw, m.mes))[:2]
        supplied = sum((m.maxima_kw for m in top), Decimal(0)) / 2
        quantities["demanda_facturable_suministrada_kw"] = str(supplied)
        supplied_origin = [m.mes for m in top]
    else:
        quantities["potencia_contratada_kw"] = str(entrada.potencia_contratada_kw)
    return {"opcion": entrada.opcion, "mes_facturacion": entrada.mes_facturacion,
        "cantidades": quantities, "meses_origen_punta": origin,
        "meses_origen_suministrada": supplied_origin, "metodo_punta": method,
        "estado": "evaluacion_con_datos_declarados", "fuente": SOURCE,
        "referencia": "Decreto 5T/2024, numerales 4.7 a 4.10, páginas 15 a 17.",
        "alcance": "No es un total en pesos ni una tarifa aprobada. Requiere verificar contrato, calendario de punta aplicable y registros de máximos integrados en 15 minutos. Los períodos deben estar imputados al mes calendario que corresponda. No cubre clientes nuevos con históricos incompletos ni condiciones especiales."}
