# schemas/cliente_schema.py
from pydantic import BaseModel
from typing import Optional

# ✅ Modelo base
class ClienteBase(BaseModel):
    nombre: str
    nit: str
    saldo_actual: Optional[int] = 0
    bloqueado: Optional[bool] = False
    minimo_alerta: int = 0
    inactivo: Optional[bool] = False

# ✅ Modelo para crear un cliente
class ClienteCreate(ClienteBase):
    pass


# ✅ Modelo para actualizar un cliente
class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    saldo_actual: Optional[int] = None
    bloqueado: Optional[bool] = None
    minimo_alerta: Optional[int] = None   # <-- Nuevo campo agregado
    inactivo: Optional[bool] = None

# ✅ Modelo de respuesta (lo que devuelve la API)
class ClienteResponse(ClienteBase):
    id: int

    class Config:
         from_attributes = True
