from sqlalchemy import Column, Integer, String, Enum
from database import Base
import enum
from sqlalchemy.orm import relationship


class RolEnum(enum.Enum):
    admin = "admin"
    usuario = "usuario"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String(100), unique=True, nullable=False)
    contrasena = Column(String(255), nullable=False)
    rol = Column(Enum(RolEnum), default=RolEnum.usuario)

    # Relación inversa para entradas realizadas
    entradas_realizadas = relationship("Entrada", back_populates="usuario") 
