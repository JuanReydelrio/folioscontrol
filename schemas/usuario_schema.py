# schemas/usuario_schema.py
# Define los modelos Pydantic para validar datos de entrada y salida de usuarios.

from pydantic import BaseModel
from typing import Optional

# ---------------------------------------------------------
# 1️⃣ Esquema base: contiene campos comunes
# ---------------------------------------------------------
class UsuarioBase(BaseModel):
    """
    Esquema base: define los atributos comunes entre todos los esquemas.
    """
    nombre_usuario: str
    rol: Optional[str] = "usuario"


# ---------------------------------------------------------
# 2️⃣ Esquema de creación: usado al registrar un nuevo usuario
# ---------------------------------------------------------
class UsuarioCreate(UsuarioBase):
    """
    Esquema que se usa cuando se crea un nuevo usuario.
    Incluye la contraseña que debe ser cifrada antes de guardar.
    """
    contrasena: str


# ---------------------------------------------------------
# 3️⃣ Esquema de login: usado para autenticación
# ---------------------------------------------------------
class UsuarioLogin(BaseModel):
    """
    Esquema para iniciar sesión.
    """
    nombre_usuario: str
    contrasena: str


# ---------------------------------------------------------
# 4️⃣ Esquema de respuesta: usado para devolver información al cliente
# ---------------------------------------------------------
class UsuarioResponse(BaseModel):
    """
    Esquema que define qué datos se devuelven en la respuesta.
    Nota: No incluye la contraseña por seguridad.
    """
    id: int
    nombre_usuario: str
    rol: str

    class Config:
        from_attributes = True  # Permite convertir modelos ORM a Pydantic
