"""Conciliación aritmética de importes declarados; no selecciona tarifas."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class InvoiceLine(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    nombre: str = Field(min_length=1, max_length=100)
    neto: Decimal = Field(ge=0, le=100000000000, decimal_places=4)
    tratamiento: Literal["afecto", "exento"]


class InvoiceInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    lineas: list[InvoiceLine] = Field(min_length=1, max_length=40)
    total_documento: Decimal = Field(ge=0, le=1000000000000, decimal_places=0)
    ajustes_finales: Decimal = Field(default=Decimal(0), ge=-100000000000, le=100000000000, decimal_places=0)


def peso(value):
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def conciliar(entrada: InvoiceInput):
    # El impuesto se calcula sobre la suma neta afecta, sin sumarlo por fila.
    afecto = sum((l.neto for l in entrada.lineas if l.tratamiento == "afecto"), Decimal(0))
    exento = sum((l.neto for l in entrada.lineas if l.tratamiento == "exento"), Decimal(0))
    neto = peso(afecto)
    iva = peso(Decimal(neto) * Decimal("0.19"))
    total = neto + iva + peso(exento) + int(entrada.ajustes_finales)
    diferencia = int(entrada.total_documento) - total
    return {"neto_afecto": neto, "exento": peso(exento), "iva": iva,
        "ajustes_finales": int(entrada.ajustes_finales), "total": total,
        "total_documento": int(entrada.total_documento), "diferencia": diferencia,
        "coincide": diferencia == 0, "lineas": [l.model_dump(mode="json") for l in entrada.lineas],
        "alcance": "Conciliación de importes netos declarados con IVA del 19 % y redondeo al peso. No verifica precios, lecturas, demanda facturable, exenciones ni aplicabilidad de una tarifa. Los ajustes finales se incorporan después del impuesto."}
