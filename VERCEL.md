# Vista previa en Vercel

Solicitud de Sebastián del 9 de noviembre de 2026: poder ver la aplicación en línea con su cuenta de Vercel. Autoriza preparar una vista previa; se mantiene pendiente el lanzamiento definitivo con tarifas oficiales aprobadas.

Proyecto: `cuentaluz-chile-preview`, equipo personal `sebastiancarrascoz-spec`, plan Hobby existente. No se contrata base de datos ni dominio. La URL y el resultado efectivo del despliegue se registran en `artifacts/vercel-preview-state.json`; no confundir una configuración preparada con una publicación verificada.

## Resultado verificado del 9 de noviembre

Sebastián autorizó expresamente el primer despliegue técnico Production del proyecto separado de pruebas. Se ejecutó con `--skip-domain`, sin promoción de dominios ni contratación de servicios. La aplicación conserva `APP_PREVIEW=1`, aviso de pruebas, `noindex`, catálogo bloqueado y cálculo sin persistencia.

- URL: https://cuentaluz-chile-preview-eep78iloq-sebastiancarrascoz-spec.vercel.app
- Despliegue: `dpl_Gdp7q3HmC1QFZxcv7oEKa5SnRufA`, estado `READY`, Python 3.12, construcción aproximada de 11,5 segundos.
- Código de aplicación desplegado: commit local `c58913fed7a739a63d4bc95b8881916e346ecdc2`.
- Se conserva la protección de Vercel Authentication: el usuario puede necesitar iniciar sesión con la cuenta propietaria para abrirlo. No se desactivó para probar.
- Salud, HTML de cuenta, CSS y worker PDF.js respondieron 200. El hash del worker coincide con el local. Precios propios: 60.750; cuenta consolidada ficticia: 13.785; catálogo no aprobado: 503; documentación API cerrada: 404. Se comprobaron `no-store`, CSP y `noindex`. Evidencia: `artifacts/vercel-http-report.json`. Estas son pruebas HTTP, sin afirmar inspección visual remota ni validación tarifaria.
- El primer intento falló porque el constructor no aceptó `-r requirements.lock`. Se conservan las mismas veinte versiones en formato plano en `requirements.txt`; `lock_runtime.py` actualiza ambos archivos y una prueba comprueba su correspondencia.
- La CLI creó un secreto de Protection Bypass for Automation al ejecutar `vercel curl`. No se imprimió ni se incorporó a Git. Se conserva para las comprobaciones autenticadas del proyecto; puede revocarse en Deployment Protection. La conexión MCP del plugin devolvió 403 para este equipo; se usó la CLI previamente autenticada, sin cambiar de cuenta ni extraer credenciales.

## Configuración

- FastAPI mediante `main.py`, Python 3.12 y dependencias de `requirements.lock`. Fuentes: [FastAPI en Vercel](https://vercel.com/docs/frameworks/backend/fastapi) y [runtime Python](https://vercel.com/docs/functions/runtimes/python).
- `vercel.json` fija `APP_ENV=production` y `APP_STORAGE=none`. La app no crea tablas ni abre conexiones de almacenamiento en ese modo. No usa una base SQLite temporal como almacenamiento persistente. Declarar también `DATABASE_URL` produce un error de configuración deliberado.
- Las funciones públicas calculan con datos de la solicitud y no guardan los formularios. Captación de correos, GPS y scrapers permanecen fuera de las rutas públicas.
- Los hosts aceptados incluyen únicamente los nombres exactos de despliegue, rama y proyecto proporcionados por las variables de sistema Vercel, además de `ALLOWED_HOSTS` cuando se configure expresamente. No se acepta `*.vercel.app`.
- La vista previa se identifica en pantalla y responde con `X-Robots-Tag: noindex, nofollow, noarchive`; `robots.txt` desautoriza indexación. Son indicaciones para buscadores, no controles de acceso. Se conserva la protección de despliegue que Vercel tenga configurada.
- `.vercelignore` excluye credenciales, bases, PDF/Excel, respaldos, artefactos y herramientas locales. Se limita `/services/` a la carpeta heredada de la raíz para conservar `app/services`, necesario para calcular.

La inspección previa reconoció FastAPI y comprobó los archivos de cálculo, configuración, plantillas y worker PDF.js. Las pruebas locales pasaron: 230 Python, cinco antiguas omitidas. Siete pruebas específicas verifican arranque sin almacenamiento, bloqueo del catálogo, cálculo, hosts, documentos API cerrados y declaración de vista previa.

## Operación

CLI de preparación: Vercel 65.12.1, instalada solo en `.qa/vercel-cli`, fuera de Git y del paquete desplegado. La autenticación la gestiona la CLI; no copiar ni imprimir tokens. Antes de desplegar, comprobar proyecto y equipo explícitos con `project inspect` y revisar `deploy --dry --json`.

Desplegar al entorno `preview` del proyecto indicado. Verificar estado final, inicio, assets locales, cuenta con precios declarados y rechazo del catálogo pendiente. Si la protección devuelve una pantalla de acceso, utilizar el mecanismo oficial de Vercel para probar el despliegue y explicar al usuario que puede necesitar iniciar sesión.

Vercel rechazó la primera petición al entorno `preview`: su CLI exige que el primer despliegue de un proyecto vacío sea `Production`. Sebastián aprobó esa excepción para este proyecto de pruebas, conservando `APP_PREVIEW=1` y `--skip-domain`. Para cambios posteriores usar preferentemente el entorno Preview y comprobar el destino antes de ejecutar. La excepción no autoriza lanzar tarifas oficiales, promover dominios, comprarlos ni contratar almacenamiento.

Las tarifas oficiales siguen pendientes y el caso Enel no está completamente validado. Para guardar datos en una futura versión se necesita un almacenamiento persistente revisado, sus controles y pruebas; no activar SQLite local dentro de las funciones.
