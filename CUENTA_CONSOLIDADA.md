# Cuenta consolidada con datos declarados

`/cuenta` permite uno o dos precios entre lecturas. Sin cambio, dejar vacíos fecha y precios nuevos. La API `/api/evaluar-cuenta` conserva los intervalos y lecturas medidos admitidos por `PeriodInput`. El período se calcula con fracciones exactas; el fijo se incorpora una sola vez, declarado o ponderado bajo un supuesto visible.

Se declaran cinco categorías: demanda, reactiva, otros afectos, otros exentos y ajustes finales. Cada una exige un importe conocido o una declaración de no aplicación con respaldo. Un faltante no se convierte en cero. Los precios son netos; el transporte debe excluir el servicio público y demás exentos declarados aparte. Las filas agregadas de ciertos pliegos no se deben sumar junto con sus componentes.

Los cargos afectos se suman antes de calcular IVA del 19 %. El redondeo por cargo o sobre subtotal se aplica al conjunto, incluida demanda. Se muestra por separado el ajuste de redondeo afecto y exento. Los ajustes finales se añaden después del impuesto, en pesos enteros y con signo; no implementan descuentos que modifican la base imponible. Un resultado negativo se rechaza. La comparación con el total de un documento no aprueba su tarifa.

## Demanda dentro de la misma cuenta

Los resultados de `/demanda` y `/demanda-3` incluyen «Incorporar demanda a mi cuenta». Una petición POST transfiere los registros; el navegador conserva el formulario sin almacenarlo en una base de datos. Los históricos se validan y recalculan al consolidar. No se confía en un total calculado en el navegador ni se suma además una demanda manual.

- 4.2/4.3: precios netos distintos para punta y potencia contratada/demanda suministrada. Los máximos y la potencia contratada admiten hasta seis decimales. La API usa `demanda4` con `datos`, ambos precios y `respaldo`.
- BT3/AT3: el resultado conserva el mínimo monetario histórico; no se reemplaza por demanda en kW multiplicada por precio actual. La API usa `demanda3` con `Demand3Input`. Una diferencia entre ventanas sin resolver impide un total único. Coincidir entre ventanas no acredita la política aplicable.
- Con demanda calculada, `adicionales.demanda.estado` debe ser `calculada`, sin importe manual. Sin históricos se admite demanda `declarado` con importe neto, o `no_aplica` sin importe. Solo demanda admite `calculada`.
- El mes de demanda debe coincidir con el mes de lectura actual: convención explícita de este escenario, pendiente de verificar la imputación efectiva de cada suministro.

La aplicabilidad de los cargos y el calendario siguen siendo declarados. No se seleccionan automáticamente FET, ETR, reactiva, subsidios, recargos de AT ni opciones especiales. No constituye aprobación comercial o industrial nacional.

## Validación

Casos ficticios independientes de precios oficiales: 100 kWh, energía neta 100/kWh, transporte 10/kWh, fijo 500 y exento 1/kWh producen neto 11.500, IVA 2.185 y total 13.785. Añadir demanda neta de 2.000 produce 16.165. Integrar 110 kW a 2.000 y punta de 70 kW a 1.000 produce 358.885. Un mínimo BT3 de 400.000 produce 489.785 con la misma base de energía. Las pruebas verifican además faltantes, duplicación, ventana ambigua, impuestos, créditos finales, precisión y transferencia de históricos.
