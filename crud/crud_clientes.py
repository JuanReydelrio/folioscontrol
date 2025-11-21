# crud/crud_clientes.py
"""
Operaciones CRUD sobre la tabla clientes.
Todas las verificaciones de permisos se hacen en las rutas (routes),
aquí sólo operaciones puras contra la base de datos.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.cliente_model import Cliente
from schemas.cliente_schema import ClienteCreate, ClienteUpdate

def create_cliente(db: Session, cliente: ClienteCreate) -> Cliente:
    """Crea un nuevo cliente. Lanza 400 si el NIT ya existe."""
    existente = db.query(Cliente).filter(Cliente.nit == cliente.nit).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un cliente con ese NIT."
        )

    nuevo = Cliente(
        nombre=cliente.nombre,
        nit=cliente.nit,
        saldo_actual=cliente.saldo_actual or 0,
        bloqueado=cliente.bloqueado or False,
        minimo_alerta=cliente.minimo_alerta,  # ← Nuevo campo
        inactivo=cliente.inactivo or False
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


def get_clientes(db: Session) -> list[Cliente]:
    """Devuelve todos los clientes."""
    return db.query(Cliente).all()


def get_cliente_by_id(db: Session, cliente_id: int) -> Cliente:
    """Devuelve un cliente por ID o lanza 404."""
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado.")
    return cliente


def update_cliente(db: Session, cliente_id: int, datos: ClienteUpdate) -> Cliente:
    """Actualiza sólo los campos enviados en datos (patch-like)."""
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado.")

    update_data = datos.dict(exclude_unset=True)

    # Si cambian NIT, verificar duplicado
    if "nit" in update_data:
        otro = db.query(Cliente).filter(
            Cliente.nit == update_data["nit"],
            Cliente.id != cliente_id
        ).first()
        if otro:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro cliente con ese NIT."
            )

    # Aplicar cambios
    for key, val in update_data.items():
        setattr(cliente, key, val)

    db.commit()
    db.refresh(cliente)
    return cliente


def delete_cliente(db: Session, cliente_id: int):
    """Elimina el cliente (si existe)."""
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado.")

    db.delete(cliente)
    db.commit()

    return {"message": f"Cliente '{cliente.nombre}' eliminado correctamente."}


def toggle_bloqueo_cliente(db: Session, cliente_id: int, bloquear: bool) -> Cliente:
    """
    Cambia el estado de 'bloqueado' de un cliente (True = bloqueado, False = desbloqueado)
    """
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado."
        )

    cliente.bloqueado = bloquear
    db.commit()
    db.refresh(cliente)
    return cliente

def toggle_inactivo_cliente(db: Session, cliente_id: int, inactivar: bool) -> Cliente:
    """
    Activa o desactiva el estado 'inactivo' de un cliente.
    True = inactivo (no debe aparecer como cliente activo en el front)
    False = activo
    """
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado."
        )

    cliente.inactivo = inactivar

    # Regla opcional (si quieres activarla)
    # Si está inactivo → también queda bloqueado automáticamente
    if inactivar:
        cliente.bloqueado = True

    db.commit()
    db.refresh(cliente)
    return cliente
