from sqlalchemy.orm import Session 
from fastapi import HTTPException
from datetime import date
from typing import List

from models.ajuste_model import Ajuste
from models.cliente_model import Cliente

from crud.crud_resumen import (
    sumar_ajuste,
    validar_mes_abierto,
    cierre_mensual_automatico,
    recalcular_saldo_resumenes
)

def validar_mes_actual(fecha: date):
    hoy = date.today()
    if fecha.year != hoy.year or fecha.month != hoy.month:
        raise HTTPException(
            status_code=409,
            detail="Solo se permiten movimientos en el mes actual."
        )   

def create_ajuste(db: Session, data, usuario_id: int):

    cliente = db.query(Cliente).filter_by(id=data.cliente_id).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    # 🔒 mismas reglas que entradas
    validar_mes_actual(data.fecha)
    cierre_mensual_automatico(db, cliente.id, data.fecha)
    validar_mes_abierto(db, cliente.id, data.fecha)

    ajuste = Ajuste(
        cliente_id=cliente.id,
        fecha=data.fecha,
        cantidad=data.cantidad,
        descripcion=data.descripcion,
    )

    try:
        # 🔥 aplicar ajuste (puede ser + o -)
        cliente.saldo_actual += data.cantidad

        db.add(ajuste)
        db.flush()

        # 🔥 impacta resúmenes
        sumar_ajuste(db, cliente.id, data.cantidad, data.fecha)

        recalcular_saldo_resumenes(
            db,
            cliente.id,
            data.fecha.year,
            data.fecha.month
        )

        db.commit()
        db.refresh(ajuste)
        return ajuste

    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Error creando ajuste: {e}")


def get_ajustes_by_cliente(db: Session, cliente_id: int) -> List[Ajuste]:
    cliente = db.query(Cliente).filter_by(id=cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    return (
        db.query(Ajuste)
        .filter(Ajuste.cliente_id == cliente_id)
        .order_by(Ajuste.id.desc())
        .all()
    )

    return ajustes
