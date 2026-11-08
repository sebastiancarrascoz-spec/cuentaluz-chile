# Revisión del cargo de demanda BT3 y AT3

Fecha: 8 de noviembre de 2026. Estado: evaluación de relaciones con históricos y precio declarados; **no es una tarifa aprobada ni el total de la cuenta**.

## Fuente y alcance

El [Decreto 5T/2024 publicado por la CNE](https://www.cne.cl/wp-content/uploads/2025/08/Decreto-5T-2024-Toma-de-razon-1.pdf), numeral 4.5, páginas 14 y 15, define el cargo BT3 mediante la comparación entre el cargo por demanda de facturación y un mínimo monetario histórico del 40 %. El numeral 4.10 extiende la forma de facturar a AT3, con sus respectivos precios. La clasificación de punta y el precio aplicable requieren el cotejo adicional del numeral 5.4. El original del decreto ya está en la biblioteca documental.

La demanda base compara el máximo leído del mes con el promedio de los dos mayores máximos mensuales de los meses que contienen horas de punta, dentro de los doce meses que incluyen el facturado. Esos máximos mensuales no deben sustituirse por máximos restringidos a horas de punta.

El mínimo monetario usa cargos históricos, conservando sus precios históricos. Reemplazarlo por el 40 % de un máximo en kW, multiplicado por el precio actual, puede producir otro importe. La app mantiene separadas la demanda base en kW, el cargo base y el incremento monetario debido al mínimo. No presenta ese incremento como potencia medida.

## Ventana del mínimo: punto pendiente de cierre

El texto revisado explicita la inclusión del mes facturado para la memoria de demanda. La expresión del mínimo monetario no lleva la misma aclaración en el párrafo consultado. La revisión realizada no encontró una instrucción primaria adicional que permita cerrar automáticamente esa diferencia de ventana para todos los suministros. No se afirma que existan dos opciones normativas libremente elegibles: son hipótesis de comprobación pendientes de cotejo.

Para evitar que una ventana elegida silenciosamente cambie el cargo, se piden doce antecedentes monetarios y el máximo del mes actual. Son trece meses consecutivos; el máximo del más antiguo no se necesita. Se comparan:

1. **Doce cargos anteriores:** se utiliza el mayor de los doce antecedentes monetarios, excluido el actual aún en evaluación.
2. **Ventana incluyendo el mes facturado:** se consideran once antecedentes y el cargo actual por determinar. Para cantidades no negativas, la ecuación `C = max(B, 0,4 × max(H, C))`, donde B es el cargo base y H el mayor antecedente, tiene solución `C = max(B, 0,4 × H)`. El resultado también conserva el mínimo que resulta al volver a incluir ese cargo calculado.

Si las dos hipótesis producen importes sin redondear diferentes y el usuario no declara una ventana confirmada para su suministro, el resultado del cargo único es nulo. Ambas alternativas permanecen visibles. Si coinciden, el importe común puede mostrarse, pero esa coincidencia no acredita la ventana ni el precio. Una ventana declarada por el usuario tampoco equivale a una validación normativa realizada por el sistema.

La incertidumbre anterior debe cerrarse con instrucciones aplicables y casos independientes antes de aprobar un perfil de producción. No se promueve BT3/AT3 a catálogo oficial por el solo funcionamiento de esta evaluación.

## Casos ficticios comprobados

| Antecedente o resultado | Caso de memoria y mínimo |
|---|---:|
| Máximo leído del mes | 50 kW |
| Dos máximos mensuales de meses con punta | 120 y 100 kW |
| Demanda base | 110 kW |
| Precio actual declarado, neto | $1.000/kW/mes |
| Cargo base, neto | $110.000 |
| Mayor cargo histórico, neto | $400.000 |
| Mínimo del 40 %, neto | $160.000 |
| Cargo resultante, neto | $160.000 |

El caso conserva 110 kW como demanda base: no inventa una medición de 160 kW para justificar el importe. Si el mes más antiguo aporta un cargo neto de $1.000.000, la primera ventana produce $400.000 mientras la segunda mantiene $160.000. Sin confirmación no se entrega un cargo único. Los importes de esta sección son ficticios y no proceden de una oferta ni de un pliego de precios vigente.

## Implementación

- `/demanda-3` ofrece el formulario de revisión; `/api/evaluar-demanda-3` recibe el esquema estructurado. Ambos mantienen `Cache-Control: no-store` y no guardan el formulario.
- Se exige BT3 o AT3, mes calendario, clasificación declarada, precio neto, doce cargos netos anteriores y los máximos de los doce meses que incluyen el actual. El calendario debe identificar al menos dos meses con punta para este alcance.
- Se rechazan meses duplicados, faltantes o ajenos al intervalo, importes negativos o no finitos y cargos actuales mezclados con antecedentes. Un dato ausente no se convierte en cero.
- El cargo del documento actual es un dato opcional separado para comparar; nunca alimenta el mínimo.
- Se identifican los meses usados en la memoria y los mayores antecedentes monetarios de cada hipótesis.
- Los productos de demanda por precio y del mínimo se calculan con fracciones exactas. El redondeo al peso se aplica al final, con mitades hacia arriba. Existe una regresión específica para importes altos cercanos al medio peso, donde un producto Decimal con precisión insuficiente puede cambiar la última unidad.
- Se usan datos de demanda ya imputados al mes calendario correspondiente. No se infieren la clasificación presente/parcialmente presente en punta ni el calendario desde los kWh mensuales.
- Quedan fuera históricos incompletos, cambios de opción, pérdidas de transformación y otras condiciones especiales de AT, además de energía, transporte, fijo, FET, exenciones, IVA y otros cargos de la cuenta.

Los perfiles aprobados siguen siendo cero. No se modificó el catálogo histórico. La biblioteca documental sigue en 362 PDF/Excel únicos.

## Verificación

El conjunto completo tiene **196 pruebas Python aprobadas, cinco omitidas por el PDF legado faltante y 10 pruebas JavaScript aprobadas**. El nuevo módulo aporta 17 pruebas Python, incluidos flujo HTML/API, errores, mínimo monetario, ventanas discordantes y precisión de productos. Los casos son sintéticos y no acreditan la aplicabilidad a una concesionaria.

La revisión de navegador local a 375, 768 y 1280 píxeles verificó el cargo común de $160.000, la ausencia de cargo único con ventanas discordantes y la selección declarada que produce $400.000. No se detectaron desbordes, errores JavaScript ni infracciones axe en los estados auditados. Se revisó la captura móvil. También se volvió a comprobar el flujo de BT/AT 4.2 y 4.3 tras generalizar la actualización de meses del formulario.

Evidencia local: `artifacts/demand3-browser.json`, `artifacts/demanda3-*` y `artifacts/demand-browser.json`. Reproducción: `scripts/verify_demand3_browser.py` y `tests/test_demand3.py`. Las pruebas visuales se ejecutan con el servidor en `127.0.0.1:8018`. Docker y despliegue remoto siguen sin probarse.
