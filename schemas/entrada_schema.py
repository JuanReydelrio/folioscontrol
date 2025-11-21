# ============================================
# schemas/entrada_schema.py
# Esquemas Pydantic para validación y respuesta
# de las entradas de folios
# ============================================

from datetime import date
from pydantic import BaseModel, Field, validator

# 🧩 Schema base (compartido)
class EntradaBase(BaseModel):
    cliente_id: int = Field(..., description="ID del cliente al que se le cargan los folios")
    fecha: date = Field(..., description="Fecha de registro de la entrada")
    cantidad: int = Field(..., gt=0, description="Cantidad de folios cargados (debe ser positiva)")
    numero_factura: str = Field(..., min_length=1, max_length=100, description="Número de factura asociado a la entrada")

    @validator("fecha")
    def validar_fecha(cls, v):
        if v > date.today():
            raise ValueError("La fecha no puede ser futura")
        return v


# 🧩 Schema para crear una nueva entrada
class EntradaCreate(EntradaBase):
    pass


# 🧩 Schema para actualizar una entrada existente
class EntradaUpdate(BaseModel):
    fecha: date | None = None
    cantidad: int | None = Field(None, gt=0)
    numero_factura: str | None = Field(None, max_length=100)


# 🧩 Schema para la respuesta completa
class EntradaResponse(EntradaBase):
    id: int
    usuario_id: int

    class Config:
         from_attributes = True

