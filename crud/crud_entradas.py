from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import date

from models.entrada_model import Entrada
from models.cliente_model import Cliente
from schemas.entrada_schema import EntradaCreate, EntradaUpdate

from crud.crud_resumen import (
    sumar_entrada,
    restar_entrada,
    recalcular_saldo_resumenes,
    validar_mes_abierto,
    cierre_mensual_automatico
)


# ======================================================
# VALIDACIÓN FUERTE: SOLO MES ACTUAL
# ======================================================
def validar_mes_actual(fecha: date):
    hoy = date.today()
    if fecha.year != hoy.year or fecha.month != hoy.month:
        raise HTTPException(
            status_code=409,
            detail="Solo se permiten movimientos en el mes actual."
        )


# ======================================================
# CREAR ENTRADA
# ======================================================
def create_entrada(db: Session, entrada_in: EntradaCreate, usuario_id: int) -> Entrada:

    cliente = db.query(Cliente).filter_by(id=entrada_in.cliente_id).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    # 🔒 VALIDACIONES CLAVE
    validar_mes_actual(entrada_in.fecha)
    cierre_mensual_automatico(db, entrada_in.cliente_id, entrada_in.fecha)
    validar_mes_abierto(db, entrada_in.cliente_id, entrada_in.fecha)

    entrada = Entrada(
        cliente_id=entrada_in.cliente_id,
        fecha=entrada_in.fecha,
        cantidad=entrada_in.cantidad,
        numero_factura=entrada_in.numero_factura,
        usuario_id=usuario_id
    )

    try:
        cliente.saldo_actual = (cliente.saldo_actual or 0) + entrada_in.cantidad

        db.add(entrada)
        db.flush()

        sumar_entrada(db, entrada.cliente_id, entrada.cantidad, entrada.fecha)
        recalcular_saldo_resumenes(
            db,
            entrada.cliente_id,
            entrada.fecha.year,
            entrada.fecha.month
        )

        db.commit()
        db.refresh(entrada)
        return entrada

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error al crear la entrada: {e}")


# ======================================================
# LISTAR / OBTENER
# ======================================================
def get_entradas(db: Session) -> List[Entrada]:
    return db.query(Entrada).order_by(Entrada.id.desc()).all()


def get_entrada_by_id(db: Session, entrada_id: int) -> Entrada:
    entrada = db.query(Entrada).filter_by(id=entrada_id).first()
    if not entrada:
        raise HTTPException(404, "Entrada no encontrada")
    return entrada


def get_entradas_by_cliente(db: Session, cliente_id: int) -> List[Entrada]:
    cliente = db.query(Cliente).filter_by(id=cliente_id).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    return (
        db.query(Entrada)
        .filter_by(cliente_id=cliente_id)
        .order_by(Entrada.id.desc())
        .all()
    )


# ======================================================
# ACTUALIZAR ENTRADA
# ======================================================
def update_entrada(db: Session, entrada_id: int, entrada_data: EntradaUpdate) -> Entrada:

    entrada = get_entrada_by_id(db, entrada_id)

    cliente = db.query(Cliente).filter_by(id=entrada.cliente_id).first()
    if not cliente:
        raise HTTPException(404, "Cliente asociado no encontrado")

    data = entrada_data.dict(exclude_unset=True)

    cantidad_original = entrada.cantidad
    fecha_original = entrada.fecha

    cantidad_nueva = data.get("cantidad", cantidad_original)
    fecha_nueva = data.get("fecha", fecha_original)
    factura_nueva = data.get("numero_factura", entrada.numero_factura)

    # 🔒 VALIDACIONES
    validar_mes_actual(fecha_nueva)
    validar_mes_abierto(db, entrada.cliente_id, fecha_nueva)

    try:
        # Revertir original
        restar_entrada(db, entrada.cliente_id, cantidad_original, fecha_original)
        cliente.saldo_actual -= cantidad_original

        # Aplicar nueva
        sumar_entrada(db, entrada.cliente_id, cantidad_nueva, fecha_nueva)
        cliente.saldo_actual += cantidad_nueva

        entrada.cantidad = cantidad_nueva
        entrada.fecha = fecha_nueva
        entrada.numero_factura = factura_nueva

        recalcular_saldo_resumenes(
            db,
            entrada.cliente_id,
            fecha_nueva.year,
            fecha_nueva.month
        )

        db.commit()
        db.refresh(entrada)
        return entrada

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error al actualizar la entrada: {e}")


# ======================================================
# ELIMINAR ENTRADA
# ======================================================
def delete_entrada(db: Session, entrada_id: int):

    entrada = get_entrada_by_id(db, entrada_id)

    cliente = db.query(Cliente).filter_by(id=entrada.cliente_id).first()
    if not cliente:
        raise HTTPException(500, "Cliente asociado no encontrado")

    # 🔒 VALIDACIONES
    validar_mes_actual(entrada.fecha)
    validar_mes_abierto(db, entrada.cliente_id, entrada.fecha)

    try:
        cliente.saldo_actual -= entrada.cantidad

        restar_entrada(db, entrada.cliente_id, entrada.cantidad, entrada.fecha)
        recalcular_saldo_resumenes(
            db,
            entrada.cliente_id,
            entrada.fecha.year,
            entrada.fecha.month
        )

        db.delete(entrada)
        db.commit()

        return {"msg": "Entrada eliminada correctamente"}

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error al eliminar la entrada: {e}")
