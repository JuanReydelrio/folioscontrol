# models/cliente_model.py
from sqlalchemy import Column, Integer, String, Boolean
from database import Base
from sqlalchemy.orm import relationship

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    nit = Column(String(50), unique=True, nullable=False)
    saldo_actual = Column(Integer, nullable=False, default=0)
    bloqueado = Column(Integer, nullable=False, default=0)
    minimo_alerta = Column(Integer, nullable=False, default=0)
    inactivo = Column(Boolean, nullable=False, default=0)
 # Relación con Entradas
    entradas = relationship(
        "Entrada",
        back_populates="cliente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # Relación con Salidas
    salidas = relationship(
        "Salida",
        back_populates="cliente",
        cascade="all, delete-orphan",
        passive_deletes=True
    )