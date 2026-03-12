# schemas/cliente_schema.py
from pydantic import BaseModel
from typing import Optional


# ======================================================
# BASE (solo para creación interna)
# ======================================================

class ClienteBase(BaseModel):

    nombre: str
    nit: str
    saldo_actual: Optional[int] = 0
    bloqueado: Optional[bool] = False
    minimo_alerta: int = 0
    inactivo: Optional[bool] = False

    valor_folio: float = 0.0
    correo_electronico: Optional[str] = None


# ======================================================
# CREAR CLIENTE
# ======================================================

class ClienteCreate(ClienteBase):
    pass


# ======================================================
# ACTUALIZAR CLIENTE
# ======================================================

class ClienteUpdate(BaseModel):

    nombre: Optional[str] = None
    saldo_actual: Optional[int] = None
    bloqueado: Optional[bool] = None
    minimo_alerta: Optional[int] = None
    inactivo: Optional[bool] = None
    valor_folio: Optional[float] = None
    correo_electronico: Optional[str] = None


# ======================================================
# RESPUESTA ADMIN (VE TODO)
# ======================================================

class ClienteResponse(BaseModel):

    id: int
    nombre: str
    nit: str
    saldo_actual: int
    bloqueado: bool
    minimo_alerta: int
    inactivo: bool
    valor_folio: float
    correo_electronico: Optional[str]

    class Config:
        from_attributes = True


# ======================================================
# RESPUESTA USUARIO (LIMITADA)
# ======================================================

class ClienteUsuarioResponse(BaseModel):

    id: int
    nombre: str
    nit: str
    saldo_actual: int
    correo_electronico: Optional[str]

    class Config:
        from_attributes = True