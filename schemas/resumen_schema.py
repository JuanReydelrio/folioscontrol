from pydantic import BaseModel
from typing import Optional

# ------- Base -------
class ResumenBase(BaseModel):
    cliente_id: int
    anio: int


# ------- Resumen Mensual -------
class ResumenMensualResponse(ResumenBase):
    mes: int
    total_facturas: int
    total_notas_credito: int
    total_notas_debito: int
    total_documentos_soporte: int
    total_nomina_electronica: int
    total_ajuste_nomina: int
    total_nota_ajuste: int
    total_entradas: int
    saldo_final: int

    class Config:
        orm_mode = True


# ------- Resumen Anual -------
class ResumenAnualResponse(ResumenBase):
    total_facturas: int
    total_notas_credito: int
    total_notas_debito: int
    total_documentos_soporte: int
    total_nomina_electronica: int
    total_ajuste_nomina: int
    total_nota_ajuste: int
    total_entradas: int
    saldo_final: int

    class Config:
        orm_mode = True
