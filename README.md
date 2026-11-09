# CuentaLuz Chile · Versión 2

Aplicación web residencial para entender el consumo, explorar un desglose y simular ahorro. FastAPI + Jinja2, CSS y JavaScript propios, sin recursos externos ni registro obligatorio.

**[Abrir versión de pruebas en Vercel](https://cuentaluz-chile-preview-eep78iloq-sebastiancarrascoz-spec.vercel.app)**. Conserva Vercel Authentication y puede pedir iniciar sesión con la cuenta propietaria. Usa precios declarados; las tarifas oficiales siguen pendientes. Configuración y pruebas en [VERCEL.md](VERCEL.md).

Actualización nacional: [362 documentos públicos respaldados y cobertura de 346 comunas](RESPALDOS_NACIONALES.md), con alcance comercial e industrial en investigación. `/fuentes` muestra los originales y sus hashes; `/revisar` concilia netos, IVA y exentos. El motor por componentes exige contexto y cantidades facturables, pero los modelos nacionales siguen pendientes de aprobación. El catálogo histórico no debe interpretarse como precio vigente.

## Ver la aplicación local

En `/demanda-3` puedes revisar el cargo de demanda neto de BT3 y AT3 con tu precio, clasificación e históricos. Se comparan la memoria en kW y el mínimo monetario; una ventana no confirmada que cambia el resultado impide emitir un cargo único. No es una tarifa aprobada ni el total de la cuenta. Alcance y verificación en [DEMANDA_BT3_AT3.md](DEMANDA_BT3_AT3.md).

En `/periodos` puedes explorar un cambio de precios entre lecturas y comparar el efecto del reparto temporal y el redondeo. Es un escenario con precios declarados; no selecciona automáticamente una tarifa oficial. El diagnóstico y las condiciones todavía pendientes están en [PRECISION_TEMPORAL.md](PRECISION_TEMPORAL.md).

En `/revisar` puedes seleccionar una factura PDF para proponer sus importes localmente, revisarlos y después comprobar el total. El archivo no se envía al servidor. La lectura admite formatos reconocibles con neto/IVA desglosados; no es una validación de tarifas y tiene límites visibles. Las pruebas del parser se ejecutan con `node --test tests/invoice_parser.test.mjs` y no necesitan un PDF privado.

En este equipo, ejecutar `Iniciar-CuentaLuz.ps1` o abrir http://127.0.0.1:8018 si el servidor ya está activo.

Instalación desde cero con Python 3.11:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8018
```

No usar el servidor de desarrollo como servicio público. Las rutas de archivos son absolutas respecto del proyecto; la base SQLite local se ubica en `data/cuentaluz.db`.

## Qué incluye

- Interfaz adaptable: inicio, calculadora por pasos, resultados, cobertura orientativa y metodología.
- Consumo directo o estimado por aparatos y días del período.
- Modelo BT1 del catálogo histórico, con fuente, vigencia declarada y advertencia explícita.
- Escenario con precio variable y cargo fijo finales ingresados por el usuario.
- Desglose reconciliado con el total, comparación con boleta, kWh/día y costo medio.
- Escenarios de reducción del 10, 20 y 30 % y control interactivo de 0 a 50 %.
- Descarga CSV con entradas y alcance; impresión o PDF desde el navegador.
- Validación de entradas, límite de cuerpo, control de hosts, cabeceras de seguridad y rutas de salud.

## Alcance tarifario

El catálogo recuperado es una referencia antigua, con diferencias entre empresas y condiciones pendientes de revisión. La versión 2 **no certifica sus importes como actuales**. El cálculo público no ofrece BT2 ni rentabilidad solar mientras se validan sus modelos. La selección de distribuidora es explícita: no se cambia automáticamente según un mapa de comunas.

Con `APP_ENV=production`, los resultados del catálogo sin aprobación documental se bloquean y la página propone usar precios propios. El cálculo personalizado es un escenario lineal, no una reproducción de todos los posibles cargos de una boleta.

## Estructura

```text
main.py                          # Aplicación, límites, cabeceras y salud
app/routes/calculator.py         # Páginas y POST /api/estimar
app/services/estimate_service.py # Contrato validado y escenarios públicos
app/services/calculator_service.py # Motor heredado, en revisión técnica
templates/                       # Cinco páginas Jinja2
static/                          # CSS, JavaScript e icono locales
config/                          # Catálogo histórico, aparatos y mapa orientativo
tests/                           # Regresiones, entradas, cálculos y controles
scripts/                         # Verificación de navegador y accesibilidad
PRODUCCION.md                    # Despliegue, pendientes y mejoras propuestas
VERIFICACION.md                  # Resultados y límites comprobados
```

## Pruebas y revisión

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m pip_audit -r requirements.lock
```

Verificación visual (servidor local activo en 8018):

```powershell
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe scripts/verify_browser.py
npm.cmd install --prefix .qa axe-core
.\.venv\Scripts\python.exe scripts/verify_accessibility.py
```

En la revisión de esta entrega, los scripts de navegador usaron Playwright 1.57 instalado en el Python local y el servidor usó el entorno aislado `.venv` con Python 3.11. Las capturas e informes se guardan en `artifacts/`, excluida de Git.

## Producción

Ver [PRODUCCION.md](PRODUCCION.md). La CI de GitHub construyó y ejecutó el contenedor, comprobó sus controles y probó respaldo/restauración y reinicio. El despliegue público y la validación de tarifas siguen pendientes. Sebastián decidió mejorar antes de publicar. La propuesta de código está en la revisión en borrador [#1](https://github.com/sebastiancarrascoz-spec/cuentaluz-chile/pull/1).

Los scrapers son herramientas de revisión: generan candidatos fuera del catálogo activo. No se programan desde el servidor web. La newsletter y el GPS heredados no están expuestos.
# Avance hacia producción

Consultar [PLAN_PRODUCCION.md](PLAN_PRODUCCION.md) para el orden solicitado y el estado real. La vista `/cuenta` reúne los cargos con datos declarados e incorpora los históricos de los módulos de demanda. La normalización inicial conserva 63.120 valores candidatos de cuatro distribuidoras, con fuente y celda. Las tarifas oficiales nacionales siguen pendientes de aprobación.
