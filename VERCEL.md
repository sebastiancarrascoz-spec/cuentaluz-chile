# Vista previa en Vercel

Solicitud de Sebastián del 9 de noviembre de 2026: poder ver la aplicación en línea con su cuenta de Vercel. Autoriza preparar una vista previa; se mantiene pendiente el lanzamiento definitivo con tarifas oficiales aprobadas.

Proyecto: `cuentaluz-chile-preview`, equipo personal `sebastiancarrascoz-spec`, plan Hobby existente. No se contrata base de datos ni dominio. La URL y el resultado efectivo del despliegue se registran en `artifacts/vercel-preview-state.json`; no confundir una configuración preparada con una publicación verificada.

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

Vercel rechazó la primera petición al entorno `preview`: su CLI exige que el primer despliegue de un proyecto vacío sea `Production`. Ese cambio requiere aprobación explícita antes de ejecutarlo; no repetir automáticamente con `--prod`. Se preparó `APP_PREVIEW=1` para mantener rótulo y `noindex` incluso si el usuario autoriza el entorno técnico Production del proyecto de pruebas. Usar `--skip-domain` para no asignar dominios automáticamente en ese primer despliegue. No promover dominios, comprarlos ni contratar almacenamiento dentro de este alcance.

Las tarifas oficiales siguen pendientes y el caso Enel no está completamente validado. Para guardar datos en una futura versión se necesita un almacenamiento persistente revisado, sus controles y pruebas; no activar SQLite local dentro de las funciones.
