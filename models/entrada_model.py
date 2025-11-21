from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Entrada(Base):
    __tablename__ = "entradas"

    id = Column(Integer, primary_key=True, index=True)
    
    cliente_id = Column(
        Integer,
        ForeignKey("clientes.id", ondelete="CASCADE"),   # 🔥 IMPORTANTE
        nullable=False
    )

    fecha = Column(Date, nullable=False)
    cantidad = Column(Integer, nullable=False)
    numero_factura = Column(String(100), nullable=False)

    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id", ondelete="SET NULL"),  # o "CASCADE", tú decides
        nullable=False
    )

    # Relaciones ORM
    cliente = relationship(
        "Cliente",
        back_populates="entradas",
        passive_deletes=True                              # 🔥 REQUERIDO PARA MySQL
    )

    usuario = relationship("Usuario", back_populates="entradas_realizadas")
