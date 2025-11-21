from pydantic import BaseModel
from models.salida_model import TipoDocumentoEnum
from datetime import date

class SalidaCreate(BaseModel):
    nit: str
    tipo_documento: TipoDocumentoEnum
    numero_documento: str
    cantidad: int = 1

class SalidaResponse(BaseModel):
    id: int
    cliente_id: int
    tipo_documento: TipoDocumentoEnum
    numero_documento: str
    fecha_documento: date
    cantidad: int

    class Config:
        from_attributes = True