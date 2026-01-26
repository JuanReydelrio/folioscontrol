#models/ajuste_model.py
from sqlalchemy import Column, Integer, Date, ForeignKey, String
from sqlalchemy.orm import relationship
from database import Base

class Ajuste(Base):
    __tablename__ = "ajustes"

    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"))
    fecha = Column(Date, nullable=False)

    cantidad = Column(Integer, nullable=False)  # 🔥 puede ser negativa
    descripcion = Column(String(255), nullable=False)


    cliente = relationship("Cliente")