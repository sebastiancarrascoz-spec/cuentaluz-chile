# Avance ordenado hacia producción

Actualización posterior del 9 de noviembre: se implementaron las siete mejoras de experiencia y revisión descritas en [MEJORAS_20261109.md](MEJORAS_20261109.md). Vista previa Vercel autorizada en proyecto separado; lanzamiento definitivo y aprobación tarifaria siguen pendientes. Esta actualización prevalece sobre las referencias anteriores a esperar hosting.

Actualizado el 8 de noviembre de 2026. Proyecto independiente de Inergy y del empleador. La instrucción de Sebastián es avanzar en este orden y mantener precisión para todas las comunas y opciones residenciales, comerciales e industriales.

| Orden | Resultado comprobado | Pendiente material |
|---|---|---|
| 1. Cerrar Enel | Conciliación de importes por 35.123; diagnóstico temporal separa los cargos y el ajuste de redondeo. | Confirmar red/área, promedio de 2025 para ETR, originales de los pliegos, aplicación temporal y redondeo. Electricidad del diagnóstico redondea a 26.301 frente a 26.300 del documento. Coincidir en total no cierra esta brecha. |
| 2. Unificar cuenta | `/cuenta` y `/api/evaluar-cuenta` integran período, energía, fijo, demanda, otros cargos, exentos, IVA y ajustes finales. Los formularios de demanda transfieren históricos y se recalculan al consolidar. | Es un escenario con datos declarados; no selecciona ni aprueba tarifas oficiales. Descuentos que reducen base imponible, condiciones especiales y otras opciones siguen fuera del cálculo automático. |
| 3. Matriz nacional | Directorio de 346 comunas. Primer lote normalizado: 63.120 valores de 12 Excel, cuatro empresas y tres meses. Matriz CSV con ausencia explícita de valores para las demás comunas. | Solo 113 CUT tienen valores en este lote; 233 no los tienen. Cinco encabezados territoriales sin correspondencia exacta; 786 incidencias. No se confunde esto con los 330 vínculos territoriales documentales del directorio. Cero perfiles oficiales aprobados. |
| 4. Corpus independiente | Una factura real anonimizada versionada, con importes esperados transcritos. Pruebas ficticias identificadas por separado para demanda y cuenta completa. | Faltan facturas reales comerciales/industriales y una muestra representativa por empresa, opción, vigencia y condiciones. Los casos ficticios y los pliegos no incrementan el corpus de facturas reales. |
| 5. Actualización controlada | Comparador por serie de cargo entre publicaciones. Octubre/noviembre: 13.626 precios modificados y 7.414 sin cambio; informe en cuarentena, sin publicación automática. | Aprobar equivalencias, impuestos, condiciones, reglas y vigencias con casos independientes antes de integrar perfiles al catálogo. |
| 6. Operación | Proceso local en modo producción verificado; respaldo SQLite y restauración aislada comprobados. Sonda de salud disponible. CI remota aprobada: construyó, arrancó, verificó, respaldó y reinició el contenedor. | Falta hosting/dominio, HTTPS, copia remota, retención y alertas reales. PostgreSQL sin prueba. Sebastián decidió seguir mejorando antes de publicar; no hay contratación ni despliegue de la web. |

## Evidencia y reproducción

- `CUENTA_CONSOLIDADA.md`: contrato del cálculo consolidado y límites.
- `NORMALIZACION_NACIONAL.md`: extracción, matriz, comparación y muestra de cotejo con PDF.
- `OPERACION.md`: respaldo, restauración de prueba, salud y proceso de lanzamiento.
- `artifacts/account-browser.json`, `artifacts/demand-browser.json`, `artifacts/demand3-browser.json`: pruebas de los flujos con datos ficticios.
- `config/normalizacion_saesa.json`: resumen versionado; los datos extensos están en `artifacts/normalizacion`, fuera de Git.
- `tests/fixtures/facturas`: corpus anonimizado y reglas de incorporación.

Se continúa trabajo independiente cuando faltan antecedentes de una etapa; eso no equivale a darla por cerrada. No se contratan servicios ni se presenta cobertura nacional exacta a partir de documentos pendientes.

## Decisiones y revisión remota

Sebastián confirmó que no conoce el promedio de 2025 ni la red del caso Enel. Esos datos permanecen pendientes, sin asumirlos. La ayuda de metodología explica su utilidad y distingue revisar importes de seleccionar una tarifa oficial.

Revisión en borrador: https://github.com/sebastiancarrascoz-spec/cuentaluz-chile/pull/1 . Rama `revision/produccion-integrada-c31b2fe`, sin fusionar a `master`. El primer commit remoto `34822ea545a695b0e6e12c47a06ba9458a26efbb` tiene el mismo árbol que el commit local `c31b2fe`. Primera CI aprobada: https://github.com/sebastiancarrascoz-spec/cuentaluz-chile/actions/runs/42510260109 . Incluyó auditoría de dependencias, construcción, arranque, controles HTTP, respaldo/restauración y reinicio del contenedor. No acredita hosting ni validación tarifaria. Las actualizaciones posteriores deben registrar su propia comprobación.
