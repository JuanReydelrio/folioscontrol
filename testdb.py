from sqlalchemy import text
from database import engine

print("Probando conexión con la base de datos...")
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Conexión exitosa:", result.scalar())
except Exception as e:
    print("❌ Error al conectar:", e)
