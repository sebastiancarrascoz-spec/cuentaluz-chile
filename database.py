import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

STORAGE_MODE = os.getenv("APP_STORAGE", "database")
if STORAGE_MODE not in ("database", "none"):
    raise RuntimeError("APP_STORAGE debe ser database o none.")
PERSISTENCE_ENABLED = STORAGE_MODE == "database"
if not PERSISTENCE_ENABLED and os.getenv("DATABASE_URL"):
    raise RuntimeError("APP_STORAGE=none no admite DATABASE_URL: revisa la configuración del entorno.")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///" + str(Path(__file__).resolve().parent / "data" / "cuentaluz.db")) if PERSISTENCE_ENABLED else "sqlite://"

# Railway entrega postgres:// pero SQLAlchemy 1.4+ requiere postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs check_same_thread=False; ignored by other DB engines
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    if not PERSISTENCE_ENABLED:
        raise RuntimeError("El almacenamiento está deshabilitado en esta vista previa.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
