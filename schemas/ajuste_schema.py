from pydantic import BaseModel
from datetime import date

class AjusteCreate(BaseModel):
    cliente_id: int
    fecha: date
    cantidad: int  # puede ser negativa
    descripcion: str


class AjusteResponse(BaseModel):
    id: int
    cliente_id: int
    fecha: date
    cantidad: int
    descripcion: str

    class Config:
        from_attributes = True
        orm_mode = True
        
