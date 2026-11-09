# Continuidad de CuentaLuz Chile

Proyecto independiente de Inergy, ARBA y del trabajo con el empleador. Leer `PRODUCCION.md` y `VERIFICACION.md` antes de continuar.

## Actualización del 9 de noviembre de 2026: vista previa Vercel

- Resultado posterior: Sebastián autorizó «Sí, desplegar el proyecto de pruebas» cuando Vercel exigió que el primer despliegue fuera Production. Se ejecutó en el proyecto separado con `--skip-domain`, `APP_PREVIEW=1` y sin contratar servicios. URL operativa protegida: https://cuentaluz-chile-preview-eep78iloq-sebastiancarrascoz-spec.vercel.app ; despliegue `dpl_Gdp7q3HmC1QFZxcv7oEKa5SnRufA`, `READY`, Python 3.12. No interpretar este Production técnico como lanzamiento tarifario aprobado.
- Pasaron comprobaciones HTTP autenticadas: salud y cuenta 200, CSS y worker 200 con hash coincidente, propios 60.750, consolidada ficticia 13.785, catálogo 503 y docs 404; `no-store`, CSP y `noindex`. No se hizo inspección visual remota. Estado y evidencias en `artifacts/vercel-preview-state.json` y `artifacts/vercel-http-report.json`.
- El constructor exigió `requirements.txt` plano: mismas veinte versiones que `requirements.lock`; script generador actualiza ambos. Nuevo test evita divergencia. Primer build fallido conservado, segundo correcto con aplicación del commit local `c58913f`.
- Vercel CLI generó un secreto de automatización al usar `vercel curl`; no se imprimió ni se guardó en Git. Vercel Authentication sigue activo. El MCP del plugin no autorizó este equipo (403); la CLI sí estaba autenticada en la cuenta propia y completó las pruebas.

- Sebastián pidió ver la app en línea y usar Vercel; confirmó que tiene cuenta. Esta solicitud autoriza una vista previa y reemplaza la espera anterior para esa finalidad. El lanzamiento definitivo, servicios pagados y tarifas oficiales siguen pendientes.
- Leer `VERCEL.md`. Proyecto verificado `cuentaluz-chile-preview`, equipo personal `sebastiancarrascoz-spec`, plan Hobby actual. La CLI ya estaba autenticada; no leer ni copiar credenciales. CLI 65.12.1 instalada en `.qa/vercel-cli`, fuera del paquete.
- Se añadió `APP_STORAGE=none`, omitiendo tablas y conexiones en arranque/salud y rechazando sesiones DB. `vercel.json` fija modo producción, cálculo sin persistencia y Python 3.12. Los hosts Vercel se aceptan por nombres exactos de variables de sistema, nunca por comodín. Vista previa con rótulo y `noindex`.
- Verificación local de adaptación: 230 pruebas Python aprobadas, cinco antiguas omitidas; siete cubren modo sin almacenamiento. La inspección del paquete comprobó fuentes de `app/services`, plantillas, catálogos y worker; excluye originales privados, DB, `.env`, respaldos, caches y herramientas.
- La existencia del proyecto no acredita despliegue funcionando. Consultar `artifacts/vercel-preview-state.json` para el resultado real y la URL cuando se completen; verificar antes de entregarla. No promover a producción como parte de esta solicitud.

## Última actualización: cuenta consolidada y normalización del 8 de noviembre de 2026

- Actualización posterior: Sebastián confirmó que no conoce red ni promedio de 2025; se mantienen pendientes y se añadió ayuda a `/metodologia#datos-suministro`. Confirmó que aún no tiene hosting/dominio y prefiere mejorar antes de publicar. No desplegar la web ni contratar servicios.
- Se creó PR en borrador #1: https://github.com/sebastiancarrascoz-spec/cuentaluz-chile/pull/1 , rama `revision/produccion-integrada-c31b2fe`. Primer commit remoto `34822ea545a695b0e6e12c47a06ba9458a26efbb`, árbol idéntico al local `c31b2fe`; las historias difieren porque la conexión creó una revisión acumulada desde `master`. No modificar ni forzar `master` ni afirmar que el local tiene upstream equivalente.
- Primera CI remota aprobada: ejecución `42510260109`. Incluyó auditoría, construcción/arranque del contenedor, controles HTTP, respaldo/restauración y reinicio. Docker sigue ausente localmente, pero el contenedor ya se comprobó en GitHub. Actualizaciones posteriores requieren su propia verificación; registrar sus SHA y ejecución.

- Sebastián autorizó avanzar con todo en orden. Leer `PLAN_PRODUCCION.md`: cerrar Enel, unificar cuenta, matriz nacional, corpus, actualización controlada y operación. No confundir avance independiente con cierre de una etapa sin antecedentes.
- `/cuenta` y `/api/evaluar-cuenta` reúnen períodos, demanda, impuestos y ajustes. Los resultados de demanda transfieren históricos por POST; se validan y recalculan al consolidar. Se rechaza la duplicación manual, los faltantes y la demanda BT3 sin resultado único. Leer `CUENTA_CONSOLIDADA.md`.
- `normalize_saesa_sources.py` extrajo 63.120 candidatos de 12 Excel oficiales de septiembre/octubre/noviembre, conservando valor XML y publicación a tres decimales. Hay 113 CUT con valores en este lote, 233 sin ellos, cinco encabezados sin equivalencia y 786 incidencias. Matriz de 346 comunas en `artifacts/normalizacion`. Ver `NORMALIZACION_NACIONAL.md`; no sumar agregados junto con sus componentes.
- `review_tariff_changes.py` comparó octubre/noviembre: 13.626 precios modificados y 7.414 sin cambio. Salida en cuarentena sin modificar el catálogo. Biblioteca aún de 362 documentos y cero perfiles aprobados.
- Corpus versionado con una factura real anonimizada; los demás ejemplos son ficticios. No afirmar que existe validación industrial independiente ni muestra nacional.
- Respaldo consistente de SQLite y restauración aislada comprobados; sonda de salud local correcta. Ver `OPERACION.md`. Se amplió CI para arrancar/reiniciar el contenedor y ejecutar controles y respaldo. Docker local no disponible; ejecución remota pendiente de comprobar.
- La pregunta por promedio de 2025 y red del caso Enel sigue pendiente de respuesta; no seleccionar ETR/red por inferencia. Se consultó también por hosting y dominio; no contratar ni suponer un destino mientras falte esa información.
- CLI GitHub activa con otra cuenta, sin escritura en el repositorio. La conexión GitHub de la aplicación sí informa administración del repositorio. No cambiar cuentas ni extraer credenciales; usar la conexión autorizada si se prepara revisión remota y registrar el resultado real.
- La vista previa actual usa `http://127.0.0.1:8018`. El cálculo público permanece declarado, sin catálogo oficial aprobado. No se modificó `config/tarifas.json`.

## Última actualización: demanda BT3 y AT3 del 8 de noviembre de 2026

- Leer `DEMANDA_BT3_AT3.md`. `/demanda-3` y `/api/evaluar-demanda-3` revisan únicamente el cargo de demanda neto, con históricos, precio y clasificación declarados. No son una cuenta completa ni una tarifa aprobada.
- La memoria en kW usa los máximos mensuales de meses con punta, dentro de doce meses incluido el actual. No sustituirlos por máximos solo en horas de punta. El mínimo del 40 % se calcula con cargos históricos en dinero, sin convertirlo en kW medidos.
- Se piden doce cargos anteriores y doce máximos mensuales que incluyen el actual: trece meses de datos, con el máximo del más antiguo opcional. El cargo actual de comparación va separado y no alimenta el mínimo.
- La ventana monetaria se conserva como pendiente: se comparan doce antecedentes y once antecedentes más el mes actual por determinar. Si difieren y no hay ventana confirmada declarada, no se devuelve un cargo único. Coincidir no aprueba la ventana. No afirmar que son dos opciones normativas libremente elegibles.
- Se calcularon productos y mínimos con fracciones exactas para evitar errores de redondeo en valores altos. El redondeo al peso es final, mitades hacia arriba.
- Verificación actual: 196 pruebas Python aprobadas, cinco omitidas; 10 JavaScript aprobadas. Navegador 375/768/1280 sin desborde, errores JS ni infracciones axe detectadas en los estados probados. También pasó nuevamente el flujo 4.2/4.3 por el ajuste del script compartido de meses.
- Pendientes materiales: cerrar ventana e interpretación aplicable con fuentes y casos independientes, validar clasificación/calendario/precios y condiciones especiales. La biblioteca sigue en 362 documentos y cero perfiles oficiales aprobados. No se modificó el catálogo ni se desplegó.

## Antecedentes: precisión temporal del 8 de noviembre de 2026

- Leer `PRECISION_TEMPORAL.md`: compara septiembre y octubre y conserva las hipótesis y brechas del diagnóstico.
- `/periodos` y `/api/evaluar-periodos` calculan escenarios con precios propios. Reparto por días o por lecturas explícitas en API; se conservan exactamente los kWh mediante fracciones. Se rechazan huecos y superposiciones de vigencia, faltantes y valores no finitos.
- El fijo se declara una sola vez o se pondera como supuesto por días del período. Se comparan redondeo por cargo y sobre subtotal, sin adjudicar un ajuste a electricidad ni aprobar precios por coincidencia del total.
- En el caso anonimizado, 7 días de septiembre y 21 de octubre dan fijo ponderado 613,9725, que redondea a 614. Por cargo el total es 35.124; sobre subtotal es 35.123 con ajuste explícito -1. La electricidad redondeada sigue en 26.301 frente a 26.300 del documento. No declarar la factura completamente validada.
- Persisten los pendientes de área, red, ETR, política de redondeo y aplicación temporal efectiva. Los valores de septiembre/octubre fueron consultados en los PDF oficiales mediante web; las descargas directas de septiembre y noviembre tampoco entregaron PDF. La biblioteca conserva 362 documentos únicos y cero perfiles aprobados.
- Verificación: 179 pruebas Python aprobadas, cinco omitidas; 10 pruebas JavaScript ya aprobadas. Navegador 375/768/1280 sin desborde, errores JS ni infracciones axe detectadas. Evidencia: `artifacts/period-browser.json`. El script de diagnóstico añade alternativas temporales y diferencias por cargo.
- El nuevo escenario no aplica automáticamente FET, ETR, demanda, reactiva, subsidios ni saldos. La investigación del recargo no habilita sustituir la fórmula heredada sin validar norma y aplicabilidad. No se modificó `config/tarifas.json` ni se publicó una versión remota.

## Antecedentes: ampliación nacional del 7 de noviembre de 2026

### Avance posterior independiente del navegador

#### Última actualización: lectura local de facturas PDF

- `/revisar` incorpora PDF.js 6.5.438 servido localmente, con licencia Apache-2.0 y hashes en `static/vendor/pdfjs/manifest.json`. No hay endpoint de carga: el PDF, su nombre y el texto completo no se transmiten. Solo los importes confirmados se envían mediante el formulario manual.
- El usuario revisa una tabla con importes y páginas antes de copiar. El lector exige neto/IVA desglosados y consistencia de cargos y total; ante faltantes, ambigüedad o cargos no reconocidos mantiene la revisión manual. No asigna diferencias a «otros». Se probó el caso privado existente, sin incorporar su archivo ni su nombre al código.
- Límites: 6 MB, 12 páginas, 200.000 caracteres y 12 segundos. Sin OCR ni lectura con contraseña. Formatos compatibles solo cuando los encabezados y la conciliación se reconocen; no afirmar cobertura de todas las empresas.
- Pruebas actuales: 165 Python aprobadas, cinco omitidas por el PDF legado faltante; 10 pruebas JavaScript aprobadas. Navegador local 375/1280: total 35.123, confirmación explícita, ninguna transmisión del PDF ni solicitudes a terceros, sin errores JS ni infracciones axe detectadas. Se comprobaron archivos inválidos, exceso de tamaño y exceso de páginas. Evidencia: `artifacts/invoice-import-browser.json`.
- Auditoría npm de las herramientas y PDF.js: cero vulnerabilidades conocidas detectadas. El proceso local de producción conserva los bloqueos del catálogo. Docker y despliegue remoto siguen sin probarse. El ZIP documental anterior no necesita contener documentos privados ni se reemplazó.
- Reproducir la lectura con `python scripts/verify_invoice_import.py ruta_al_pdf_local_de_prueba`. CI ejecuta también `node --test tests/invoice_parser.test.mjs`; no requiere la factura privada. Para reconstruir el vendor, usar `scripts/vendor_pdfjs.py` tras instalar la versión exacta con npm en `.qa`.

#### Antecedentes del módulo de demandas

- `/demanda` y `/api/evaluar-demanda` evalúan cantidades para BT4.2, BT4.3, AT4.2 y AT4.3 a partir de históricos y calendario declarados. Se accede desde `/revisar`. No devuelven precios ni aprueban tarifas.
- Fuente: Decreto 5T/2024, numerales 4.7 a 4.10, páginas 15 a 17, original ya respaldado con SHA-256. El calendario de punta lo declara el usuario; no se supone un calendario nacional. El formulario pide el período de punta anterior completo fuera de punta.
- Se exigen 12 meses consecutivos, incluido el facturado. No se sustituyen faltantes por cero. Punta no puede superar el máximo mensual. En 4.2 se pide potencia contratada; en 4.3 se promedian los dos mayores máximos suministrados del histórico.
- Resultado actual: 164 pruebas pasan y cinco se omiten. Navegador local a 375/768/1280 sin desborde ni infracciones axe detectadas. Caso ficticio: máximos 120/100 kW producen 110 kW suministrados; punta anterior 80/60 produce 70 kW. Evidencia: `artifacts/demand-browser.json` y capturas `demanda-*`.
- Pendientes: calendarios oficiales por sistema, condiciones especiales, clientes sin histórico completo, BT3/AT3 y su piso monetario, otras opciones, precios y validación industrial independiente. Este módulo de cantidades no constituye una calculadora monetaria nacional aprobada.

### Antecedentes de la recopilación nacional

- Leer primero `RESPALDOS_NACIONALES.md`: prevalece para cobertura, fuentes y precisión sobre el alcance inicial BT1 de la v2. Sebastián pidió todas las tarifas, incluidas comerciales e industriales y todas las comunas.
- Se respaldaron 362 PDF/Excel únicos con SHA-256 en `artifacts/fuentes_nacionales`; `config/fuentes_nacionales.json` es solo el índice documental. Los originales no están en Git. No confundir documentos respaldados con modelos aprobados: siguen siendo cero.
- Paquete independiente: `C:\Users\sncar\cuentaluz-respaldos\CuentaLuz-fuentes-publicas-20261107T232713Z.zip`, 467 archivos comprobados, SHA-256 `97577f9ba580c73877dfbb4158b50d12bd4c027d7d0a990854d500c1247341a4`. Hay un archivo `.zip.sha256` junto al ZIP. No contiene boletas privadas. Es un respaldo local, no una copia remota.
- El directorio público usa `config/cobertura_nacional.json`: 346 comunas, 330 asociadas documentalmente y 16 pendientes; 117 admiten varias empresas. No volver a usar el mapa legado de cuatro distribuidoras para resolver suministros.
- La factura privada indicada por Sebastián está fuera de Git. El caso anonimizado de 145 kWh suma 35.123 y el histórico calcula 30.250. `/revisar` concilia sus importes exactamente; no valida precios.
- El perfil candidato Enel octubre, Macul, BT_AA, T1 calcula 35.124 en un escenario interno: no está aprobado. Falta el PDF original descargable, pliego de septiembre, regla temporal, red/sector/tramo y explicar un peso de diferencia en fijo. No afirmar que el error del catálogo nacional está resuelto ni promover ese candidato a noviembre.
- `tariff_engine.py` es la base decimal por componentes y cantidades facturables. No deriva demanda desde kWh. La aprobación exige evidencia y revisión; `revision_interna` es únicamente diagnóstico local, nunca un parámetro HTTP.
- La página inicial usa precios propios por defecto. Producción bloquea referencias sin aprobar. Mantener estas barreras al incorporar pliegos.
- Verificación actual: 150 pruebas pasan y cinco se omiten por faltar el PDF de Enel del extractor legado. Flujos nacionales sin desborde en 375/768/1280/1920; axe sin infracciones detectadas en seis páginas, con contraste decorativo incompleto.
- Los siguientes pendientes materiales son completar fuentes bloqueadas/parciales, conciliar nombres legales y aprobar fórmulas por período y familia con casos independientes. El diseño y el respaldo nacional no acreditan una calculadora nacional lista para producción.

## Antecedentes de la v2 inicial

- La rama `mejora/produccion-v2` contiene el rediseño del 7 de noviembre de 2026. El commit inicial preserva el desarrollo recuperado.
- La vista previa local usa `127.0.0.1:8018`; el proceso no debe exponerse como servicio de producción.
- No presentar el catálogo histórico como vigente. Un scraper prepara candidatos; la aprobación requiere pliego, condiciones y casos contrastados. BT2 y solar no forman parte de la experiencia pública validada.
- El modo producción bloquea referencias sin aprobar y permite escenarios con precios propios. Conservar este control al ampliar el catálogo.
- La interfaz utiliza CSS y JavaScript locales. Mantener accesibilidad por teclado, límites de entrada y trazabilidad dentro del resultado y sus exportaciones.
- Ejecutar las pruebas apropiadas con Python 3.11 en `.venv`. La verificación visual utiliza los scripts en `scripts/` y guarda evidencia en `artifacts/`.
- No incorporar credenciales, bases de datos, boletas identificables, artefactos de prueba ni archivos `.env` a Git.
- Actualizar los resultados comprobados y pendientes reales después de cambios relevantes. No confundir la prueba local del proceso con una prueba del contenedor, de PostgreSQL o del hosting.
