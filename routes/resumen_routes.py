# routes/resumen_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db

from crud.crud_resumen import (
    resumen_mensual_por_nit,
    resumen_anual_por_nit,
    cerrar_mes,
    cerrar_anio
)

router = APIRouter(
    prefix="/resumenes",
    tags=["Resúmenes"]
)


# ======================================================
#     📌 Obtener resumen mensual por NIT
# ======================================================
@router.get("/mensual/{nit}")
def get_resumen_mensual(nit: str, anio: int, mes: int, db: Session = Depends(get_db)):
    """
    Consulta un resumen mensual por NIT, año y mes.
    """
    resumen = resumen_mensual_por_nit(db, nit, anio, mes)

    if not resumen:
        raise HTTPException(
            status_code=404,
            detail="No existe resumen para ese NIT, año y mes."
        )

    return resumen


# ======================================================
#     📌 Obtener resumen anual por NIT
# ======================================================
@router.get("/anual/{nit}")
def get_resumen_anual(nit: str, anio: int, db: Session = Depends(get_db)):
    """
    Consulta un resumen anual por NIT y año.
    """
    resumen = resumen_anual_por_nit(db, nit, anio)

    if not resumen:
        raise HTTPException(
            status_code=404,
            detail="No existe resumen anual para ese NIT y año."
        )

    return resumen


# ======================================================
#     📌 Cerrar mes (guardar saldo_final)
# ======================================================
@router.post("/cerrar-mes/{cliente_id}")
def cerrar_mes_endpoint(cliente_id: int, anio: int, mes: int, db: Session = Depends(get_db)):
    """
    Cierra un mes para un cliente, guardando su saldo_final real.
    """
    resumen = cerrar_mes(db, cliente_id, anio, mes)

    if not resumen:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado."
        )

    return {"msg": "Mes cerrado correctamente", "resumen": resumen}


# ======================================================
#     📌 Cerrar año (guardar saldo_final anual)
# ======================================================
@router.post("/cerrar-anio/{cliente_id}")
def cerrar_anio_endpoint(cliente_id: int, anio: int, db: Session = Depends(get_db)):
    """
    Cierra el año para un cliente, guardando su saldo_final anual.
    """
    resumen = cerrar_anio(db, cliente_id, anio)

    if not resumen:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado."
        )

    return {"msg": "Año cerrado correctamente", "resumen": resumen}