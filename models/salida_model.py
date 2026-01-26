# models/salida_model.py
from sqlalchemy import Column, Integer, String, Enum, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import date


class TipoDocumentoEnum(str, enum.Enum):
    FACTURA = "FACTURA"
    NOTA_CREDITO = "NOTA_CREDITO"
    NOTA_DEBITO = "NOTA_DEBITO"
    DOCUMENTO_SOPORTE = "DOCUMENTO_SOPORTE"
    AJUSTE_DOCUMENTO_SOPORTE = "AJUSTE_DOCUMENTO_SOPORTE"  # 👈 NUEVO
    NOMINA_ELECTRONICA = "NOMINA_ELECTRONICA"
    AJUSTE_NOMINA = "AJUSTE_NOMINA"
    NOTA_AJUSTE = "NOTA_AJUSTE"


class Salida(Base):
    __tablename__ = "salidas"

    id = Column(Integer, primary_key=True, index=True)

    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)

    tipo_documento = Column(Enum(TipoDocumentoEnum), nullable=False)

    numero_documento = Column(String(150), nullable=False)

    fecha_documento = Column(Date, default=date.today, nullable=False)

    cantidad = Column(Integer, nullable=False, default=1)

    # Relación con Cliente
    cliente = relationship("Cliente", back_populates="salidas")