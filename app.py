# app.py
# Punto de entrada principal del backend FastAPI.
# Aquí se inicializa la app, se crean las tablas y se incluyen los routers (rutas API).

from fastapi import FastAPI
from database import Base, engine
from routes import usuarios_routes
from routes import usuarios_routes, clientes_routes, entrada_routes,salida_routes, resumen_routes



# 🔹 Crear las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)

# 🔹 Inicializar la app FastAPI
app = FastAPI(
    title="API Control de Folios Electrónicos",
    description="Sistema backend para gestión de usuarios y control de folios",
    version="1.0.0"
)

# 🔹 Registrar los routers (endpoints del sistema)
app.include_router(usuarios_routes.router)
app.include_router(usuarios_routes.router)
app.include_router(clientes_routes.router)
app.include_router(entrada_routes.router)
app.include_router(salida_routes.router)
app.include_router(resumen_routes.router)


# 🔹 Ruta raíz de prueba
@app.get("/")
def root():
    return {"message": "🚀 API de Control de Folios funcionando correctamente"}
