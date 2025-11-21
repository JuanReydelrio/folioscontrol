# crud/crud_entradas.py

from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models.entrada_model import Entrada
from models.cliente_model import Cliente
from schemas.entrada_schema import EntradaCreate, EntradaUpdate

from crud.crud_resumen import (
    sumar_entrada,
    restar_entrada,
    recalcular_saldo_resumenes
)


# ======================================================
#                   CREAR ENTRADA
# ======================================================
def create_entrada(db: Session, entrada_in: EntradaCreate, usuario_id: int) -> Entrada:

    cliente = db.query(Cliente).filter(Cliente.id == entrada_in.cliente_id).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    entrada = Entrada(
        cliente_id=entrada_in.cliente_id,
        fecha=entrada_in.fecha,
        cantidad=entrada_in.cantidad,
        numero_factura=entrada_in.numero_factura,
        usuario_id=usuario_id
    )

    try:
        # Ajustar saldo del cliente
        cliente.saldo_actual = (cliente.saldo_actual or 0) + entrada_in.cantidad

        db.add(entrada)

        # Resumen mensual/anual
        sumar_entrada(db, entrada.cliente_id, entrada.cantidad, entrada.fecha)

        # Recalcular saldo final mensual y anual
        recalcular_saldo_resumenes(db, entrada.cliente_id, entrada.fecha.year, entrada.fecha.month)

        db.commit()
        db.refresh(entrada)

        return entrada

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error al crear la entrada: {e}")


# ======================================================
#                   LISTAR / OBTENER
# ======================================================
def get_entradas(db: Session) -> List[Entrada]:
    return db.query(Entrada).order_by(Entrada.id.desc()).all()


def get_entrada_by_id(db: Session, entrada_id: int) -> Entrada:
    entrada = db.query(Entrada).filter(Entrada.id == entrada_id).first()
    if not entrada:
        raise HTTPException(404, "Entrada no encontrada")
    return entrada


def get_entradas_by_cliente(db: Session, cliente_id: int) -> List[Entrada]:
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return (
        db.query(Entrada)
        .filter(Entrada.cliente_id == cliente_id)
        .order_by(Entrada.id.desc())
        .all()
    )


# ======================================================
#                   ACTUALIZAR ENTRADA
# ======================================================
def update_entrada(db: Session, entrada_id: int, entrada_data: EntradaUpdate) -> Entrada:
    entrada = get_entrada_by_id(db, entrada_id)

    cliente = db.query(Cliente).filter(Cliente.id == entrada.cliente_id).first()
    if not cliente:
        raise HTTPException(404, "Cliente asociado no encontrado")

    data = entrada_data.dict(exclude_unset=True)

    cantidad_original = entrada.cantidad
    fecha_original = entrada.fecha

    cantidad_nueva = data.get("cantidad", cantidad_original)
    fecha_nueva = data.get("fecha", fecha_original)
    factura_nueva = data.get("numero_factura", entrada.numero_factura)

    try:
        # --------------------------
        # CASO 1: NO CAMBIA FECHA NI CANTIDAD
        # --------------------------
        if cantidad_nueva == cantidad_original and fecha_nueva == fecha_original:
            entrada.numero_factura = factura_nueva
            db.commit()
            db.refresh(entrada)
            return entrada

        # --------------------------
        # CASO 2: REVERSAR ENTRADA ORIGINAL
        # --------------------------
        restar_entrada(db, entrada.cliente_id, cantidad_original, fecha_original)
        cliente.saldo_actual -= cantidad_original

        # --------------------------
        # CASO 3: APLICAR ENTRADA NUEVA
        # --------------------------
        sumar_entrada(db, entrada.cliente_id, cantidad_nueva, fecha_nueva)
        cliente.saldo_actual += cantidad_nueva

        # --------------------------
        # ACTUALIZAR REGISTRO ENTRADA
        # --------------------------
        entrada.cantidad = cantidad_nueva
        entrada.fecha = fecha_nueva
        entrada.numero_factura = factura_nueva

        # Recalcular saldo mensual/anual
        recalcular_saldo_resumenes(db, entrada.cliente_id, fecha_nueva.year, fecha_nueva.month)

        db.commit()
        db.refresh(entrada)
        return entrada

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error al actualizar la entrada: {e}")


# ======================================================
#                   ELIMINAR ENTRADA
# ======================================================
def delete_entrada(db: Session, entrada_id: int):
    entrada = get_entrada_by_id(db, entrada_id)

    cliente = db.query(Cliente).filter(Cliente.id == entrada.cliente_id).first()
    if not cliente:
        raise HTTPException(500, "Cliente asociado no encontrado")

    try:
        # Revertir saldo
        cliente.saldo_actual -= entrada.cantidad

        # Revertir en resumen mensual/anual
        restar_entrada(db, entrada.cliente_id, entrada.cantidad, entrada.fecha)

        # Recalcular saldo final
        recalcular_saldo_resumenes(db, entrada.cliente_id, entrada.fecha.year, entrada.fecha.month)

        db.delete(entrada)
        db.commit()

        return {"msg": "Entrada eliminada correctamente"}

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error al eliminar la entrada: {e}")
