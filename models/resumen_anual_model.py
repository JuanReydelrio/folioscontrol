# models/resumen_anual_model.py
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class ResumenAnual(Base):
    __tablename__ = "resumen_anual"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    anio = Column(Integer, nullable=False)

    total_facturas = Column(Integer, default=0)
    total_notas_credito = Column(Integer, default=0)
    total_notas_debito = Column(Integer, default=0)
    total_documentos_soporte = Column(Integer, default=0)
    total_ajuste_documentos_soporte = Column(Integer, default=0)
    total_nomina_electronica = Column(Integer, default=0)
    total_ajuste_nomina = Column(Integer, default=0)
    total_nota_ajuste = Column(Integer, default=0)
    total_entradas = Column(Integer, default=0)

    total_ajustes = Column(Integer, default=0)

    saldo_inicial = Column(Integer, default=0)
    saldo_final = Column(Integer, default=0)

    cliente = relationship("Cliente")

    __table_args__ = (
        UniqueConstraint("cliente_id", "anio", name="uq_resumen_anual"),
    )
