# Precisión temporal y redondeo

Revisión: 8 de noviembre de 2026. Los escenarios siguientes son diagnósticos; **no aprueban una tarifa ni acreditan la política de facturación de Enel**.

## Hallazgo del caso de prueba

El documento anonimizado corresponde a 145 kWh entre lecturas del 23 de septiembre y el 21 de octubre de 2026. El catálogo histórico devuelve 30.250 frente a 35.123 del documento. La revisión de sus importes netos y exentos reconstruye el documento exactamente, pero eso no verifica sus precios.

Los pliegos oficiales de [septiembre](https://www.enel.cl/content/dam/enel-cl/es/personas/informacion-de-utilidad/tarifas-y-reglamentos/tarifas/tarifas-reguladas/2026/Enel%20Distribuci%C3%B3n%20Chile%20SA._Tarifas%20Suministro%20El%C3%A9ctrico%208T_%20VAD%205T%20Septiembre%20de%202026.pdf) y [octubre](https://www.enel.cl/content/dam/enel-cl/es/personas/informacion-de-utilidad/tarifas-y-reglamentos/tarifas/tarifas-reguladas/2026/Enel%20Distribuci%C3%B3n%20Chile%20SA._Tarifas%20Suministro%20El%C3%A9ctrico%208T_%20VAD%205T%20Octubre%20de%202026.pdf), página 1, para la columna Macul y el escenario BT_AA/T1 contienen estos precios netos:

| Precio | Septiembre | Octubre |
|---|---:|---:|
| Energía, $/kWh | 136,169 | 136,169 |
| Compras de potencia, $/kWh | 25,078 | 25,078 |
| Distribución, $/kWh | 20,160 | 20,129 |
| Electricidad consumida: suma anterior, $/kWh | 181,407 | 181,376 |
| Transporte, $/kWh | 17,218 | 17,218 |
| Administración, $/mes publicado | 611,118 | 614,924 |
| Servicio público exento, $/kWh | 0,855 | 0,855 |

Los PDF fueron consultados mediante la herramienta web. Las descargas directas nuevas de septiembre y noviembre tampoco entregaron un PDF reconocible; quedaron registradas como fallidas. No se cuentan como originales respaldados ni se inventa su SHA-256. La biblioteca sigue conteniendo 362 PDF/Excel únicos.

## Qué cambia al considerar ambos meses

La convención explícita de este diagnóstico excluye la fecha de lectura anterior e incluye la actual: 28 días, siete de septiembre y 21 de octubre. Esta convención debe cotejarse con la distribuidora; la coincidencia numérica no la demuestra.

El [Decreto 5T/2024](https://www.cne.cl/wp-content/uploads/2025/08/Decreto-5T-2024-Toma-de-razon-1.pdf), numeral 5.1, página 17, contempla la estimación de consumos de meses calendario en proporción a sus días. El original del decreto está respaldado. Esa regla de reparto de energía no acredita por sí sola la aplicación temporal del fijo, los precios ni los redondeos.

Con reparto uniforme por días, los consumos estimados son 36,25 y 108,75 kWh. Se conserva exactamente su suma. Ponderar además los dos precios fijos por 7/28 y 21/28 es un **supuesto del escenario**, no una regla verificada: produce 613,9725, que redondea a 614.

| Cálculo | Electricidad redondeada | Fijo redondeado | Neto afecto | IVA | Exento | Total |
|---|---:|---:|---:|---:|---:|---:|
| Solo octubre, por cargo | 26.300 | 615 | 29.412 | 5.588 | 124 | 35.124 |
| Ambos meses, por cargo | 26.301 | 614 | 29.412 | 5.588 | 124 | 35.124 |
| Ambos meses, sobre subtotal afecto | 26.301 | 614 | 29.411 | 5.588 | 124 | 35.123 |
| Documento de prueba | 26.300 | 614 | 29.411 | 5.588 | 124 | 35.123 |

El transporte redondeado es 2.497 en todos los casos. En el escenario sobre subtotal, la suma de los cargos redondeados excede en un peso el neto afecto calculado desde los importes sin redondear. La app muestra ese ajuste de -1 por separado; no lo presenta como descuento ni lo asigna a electricidad para reproducir su línea.

La coincidencia de 35.123 bajo una de las hipótesis **no cierra la validación**: la electricidad redondeada sigue difiriendo en un peso del documento. Faltan la política efectiva de redondeo y agregación, la aplicación temporal de precios y fijo y la confirmación del área, red y ETR T1. T1 depende del promedio del año anterior; no se deduce de los 145 kWh del mes.

## Implementación y controles

`/periodos` permite un escenario con dos precios declarados y un cambio dentro del intervalo. No carga automáticamente los precios del caso de prueba. `/api/evaluar-periodos` admite hasta 24 vigencias, con reparto por días o consumos medidos por intervalo que deben sumar el total.

- Las fechas de vigencia incluyen ambos extremos; las lecturas usan el intervalo anterior descrito.
- Se rechazan huecos, superposiciones, intervalos invertidos o ajenos al período, consumos no finitos y fechas fuera del límite admitido.
- El motor usa fracciones racionales para conservar exactamente energía y productos precio por consumo. La tabla muestra seis decimales; los redondeos monetarios usan mitades hacia arriba.
- Las componentes variables se acumulan antes de redondearse. Dividir un precio idéntico en varios intervalos no duplica el fijo ni altera el total.
- El fijo se declara una sola vez para todo el período o se pondera explícitamente como hipótesis. Nunca se cobra un fijo completo por cada fragmento.
- Se muestran ambas alternativas de redondeo y el ajuste del subtotal. No se selecciona una política por su coincidencia con la factura.
- IVA del 19 % sobre el neto afecto redondeado; los exentos se mantienen separados. No se aplican automáticamente FET, ETR, potencias, reactiva, subsidios, saldos ni condiciones particulares.

El perfil oficial aprobado continúa siendo un control distinto de este escenario de precios propios. No se modificó `config/tarifas.json` ni se promovieron candidatos de Enel. El diagnóstico se reproduce con `scripts/diagnose_invoice_case.py`; los resultados anonimizados quedan en `artifacts/boleta-revision/diagnostico_anonimizado.json`.
