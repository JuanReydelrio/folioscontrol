from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.cliente_model import Cliente
from models.usuario_model import RolEnum, Usuario
from security import get_current_user

from crud.crud_resumen import (
    resumen_mensual_por_nit,
    resumen_anual_por_nit,
    cierre_anual_manual,
    resumenes_mensuales_anio_por_nit
)

from fastapi import HTTPException, status

def require_admin(usuario = Depends(get_current_user)):
    if usuario.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: solo administradores"
        )
    return usuario


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
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
  # 🔒 Usuario normal solo puede ver su cliente
    if usuario.rol != RolEnum.admin:

        cliente = db.query(Cliente).filter_by(id=usuario.cliente_id).first()

        if not cliente:
            raise HTTPException(404, "Cliente no encontrado")

        nit = cliente.nit

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
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    if usuario.rol != RolEnum.admin:

        cliente = db.query(Cliente).filter_by(id=usuario.cliente_id).first()

        if not cliente:
            raise HTTPException(404, "Cliente no encontrado")

        nit = cliente.nit

    resumen = resumen_anual_por_nit(db, nit, anio)

    if not resumen:
        raise HTTPException(404, "No existe resumen anual")

    return resumen



# ======================================================
# 📊 RESÚMENES MENSUALES DEL AÑO
# ======================================================
@router.get("/mensuales/{nit}")
def get_resumenes_mensuales_anio(
    nit: str,
    anio: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):

    if usuario.rol != RolEnum.admin:

        cliente = db.query(Cliente).filter_by(id=usuario.cliente_id).first()

        if not cliente:
            raise HTTPException(404, "Cliente no encontrado")

        nit = cliente.nit

    return resumenes_mensuales_anio_por_nit(db, nit, anio)



# ======================================================
# 🔒 CIERRE ANUAL GLOBAL
# ======================================================
@router.post("/cerrar-anio")
def cerrar_anio_global(
    anio: int,
    db: Session = Depends(get_db),
    _ = Depends(require_admin)
):
    return cierre_anual_manual(db, anio)
