from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db

from crud.crud_resumen import (
    resumen_mensual_por_nit,
    resumen_anual_por_nit,
    cierre_anual_manual,
    resumenes_mensuales_anio_por_nit
)

router = APIRouter(
    prefix="/resumenes",
    tags=["Resúmenes"]
)

# ======================================================
# 📌 RESUMEN MENSUAL POR NIT
# ======================================================
@router.get("/mensual/{nit}")
def get_resumen_mensual(
    nit: str,
    anio: int,
    mes: int,
    db: Session = Depends(get_db)
):
    resumen = resumen_mensual_por_nit(db, nit, anio, mes)

    if not resumen:
        raise HTTPException(404, "No existe resumen mensual")

    return resumen


# ======================================================
# 📌 RESUMEN ANUAL POR NIT
# ======================================================
@router.get("/anual/{nit}")
def get_resumen_anual(
    nit: str,
    anio: int,
    db: Session = Depends(get_db)
):
    resumen = resumen_anual_por_nit(db, nit, anio)

    if not resumen:
        raise HTTPException(404, "No existe resumen anual")

    return resumen


# ======================================================
# 🔒 CIERRE ANUAL GLOBAL (ADMIN)
# ======================================================
@router.post("/cerrar-anio")
def cerrar_anio_global(
    anio: int,
    db: Session = Depends(get_db)
):
    return cierre_anual_manual(db, anio)
# ======================================================
# 📊 Resúmenes mensuales de TODO el año por NIT
# ======================================================
@router.get("/mensuales/{nit}")
def get_resumenes_mensuales_anio(
    nit: str,
    anio: int,
    db: Session = Depends(get_db)
):
    """
    Devuelve los 12 resúmenes mensuales de un año para un cliente.
    """
    return resumenes_mensuales_anio_por_nit(db, nit, anio)
