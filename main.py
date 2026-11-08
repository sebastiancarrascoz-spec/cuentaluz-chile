"""CuentaLuz: interfaz pública, API y controles operativos."""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
from database import Base, engine
from app.routes import calculator
import app.models.subscriber  # registra tablas existentes sin captar datos
import app.models.sec_cache

PRODUCTION = os.getenv("APP_ENV", "development") == "production"
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    # Los scrapers nunca publican tarifas desde el proceso web.
    yield
    engine.dispose()


app = FastAPI(title="CuentaLuz Chile", version="2.0.0", lifespan=lifespan,
    docs_url=None if PRODUCTION else "/docs", redoc_url=None,
    openapi_url=None if PRODUCTION else "/openapi.json")
hosts = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",") if h.strip()]
if PRODUCTION and (not os.getenv("ALLOWED_HOSTS") or "*" in hosts):
    raise RuntimeError("Configura ALLOWED_HOSTS con el dominio público antes de iniciar en producción.")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)


class RequestControls:
    """Límite real del cuerpo aun sin Content-Length; cabeceras en toda respuesta."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id = uuid4().hex
        async def secured_send(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                policy = "default-src 'self'; script-src 'self'; worker-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
                headers.extend([(b"x-content-type-options", b"nosniff"), (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"permissions-policy", b"geolocation=(), camera=(), microphone=()"),
                    (b"content-security-policy", policy.encode()), (b"x-request-id", request_id.encode())])
                if scope["path"] in ("/calcular", "/api/estimar", "/revisar", "/api/conciliar", "/demanda", "/api/evaluar-demanda", "/periodos", "/api/evaluar-periodos", "/demanda-3", "/api/evaluar-demanda-3", "/cuenta", "/api/evaluar-cuenta", "/cuenta/preparar-demanda"):
                    headers.append((b"cache-control", b"no-store"))
                if PRODUCTION:
                    headers.append((b"strict-transport-security", b"max-age=31536000"))
                message["headers"] = headers
            await send(message)
        # Acumular únicamente peticiones pequeñas de formulario o JSON.
        chunks = []
        size = 0
        if scope["method"] in ("POST", "PUT", "PATCH"):
            while True:
                part = await receive()
                if part["type"] == "http.disconnect":
                    return
                size += len(part.get("body", b""))
                if size > 32768:
                    response = JSONResponse({"detail": "La solicitud supera el tamaño permitido."}, status_code=413)
                    return await response(scope, receive, secured_send)
                chunks.append(part.get("body", b""))
                if not part.get("more_body", False):
                    break
            body = b"".join(chunks)
            delivered = False
            async def buffered_receive():
                nonlocal delivered
                if not delivered:
                    delivered = True
                    return {"type": "http.request", "body": body, "more_body": False}
                return await receive()
            return await self.app(scope, buffered_receive, secured_send)
        await self.app(scope, receive, secured_send)


app.add_middleware(RequestControls)
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")
app.include_router(calculator.router)


@app.exception_handler(RequestValidationError)
async def invalid_input(request, exc):
    # No reflejar valores del usuario ni NaN/Infinity en la respuesta JSON.
    return JSONResponse({"detail": [{"campo": ".".join(str(x) for x in e["loc"]),
        "mensaje": "Valor no válido o fuera del rango permitido."} for e in exc.errors()]}, status_code=422)


@app.get("/health/live", include_in_schema=False)
def live():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/health/ready", include_in_schema=False)
def ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        from app.services.estimate_service import EstimateInput, estimar
        result = estimar(EstimateInput(kwh=250))
        return {"status": "ok", "catalogo": result["tarifa"]["estado"], "modelo_publico": "Escenarios con precios propios y conciliación; catálogo oficial pendiente"}
    except Exception:
        logger.exception("Fallo de disponibilidad")
        return JSONResponse({"status": "unavailable"}, status_code=503)


@app.get("/robots.txt", include_in_schema=False)
def robots(request: Request):
    return PlainTextResponse("User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /calcular\nSitemap: " + str(request.base_url) + "sitemap.xml\n")


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap(request: Request):
    from xml.sax.saxutils import escape
    base = str(request.base_url).rstrip("/")
    urls = "".join("<url><loc>" + escape(base + path) + "</loc></url>" for path in ("/", "/comunas", "/metodologia", "/fuentes", "/revisar"))
    return Response('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + urls + '</urlset>', media_type="application/xml")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=int(os.getenv("PORT", "8018")), reload=not PRODUCTION)
