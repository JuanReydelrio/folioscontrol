# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Carga las variables del archivo .env si existe
load_dotenv()

DB_USER = os.getenv("DB_USER", "u775841278_hrey")
DB_PASS = os.getenv("DB_PASSWORD", "Dreams1016")  # usualmente vacío en XAMPP
DB_HOST = os.getenv("DB_HOST", "srv1769.hstgr.io")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "u775841278_folios_app")  # cambia por el nombre real de tu BD

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# crea el motor de conexión
engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

# crea la sesión (para interactuar con la BD)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# clase base para modelos ORM
Base = declarative_base()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()