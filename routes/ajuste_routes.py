#
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from security import get_current_user
from models.usuario_model import Usuario

from schemas.ajuste_schema import (
    AjusteCreate,
    AjusteResponse
)

from crud.curd_ajustes import (
    create_ajuste,
    get_ajustes_by_cliente
)

router = APIRouter(
    prefix="/ajustes",
    tags=["Ajustes"]
)

# ======================================================
# 🔒 SOLO ADMIN
# ======================================================
def require_admin(usuario: Usuario = Depends(get_current_user)):
    if usuario.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: solo administradores."
        )
    return usuario


# ======================================================
# ➕ CREAR AJUSTE
# ======================================================
@router.post(
    "/",
    response_model=AjusteResponse,
    status_code=status.HTTP_201_CREATED
)
def crear_ajuste(
    data: AjusteCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)
):
    return create_ajuste(db, data, usuario.id)


# ======================================================
# 📄 LISTAR AJUSTES POR CLIENTE
# ======================================================
@router.get(
    "/cliente/{cliente_id}",
    response_model=List[AjusteResponse]
)
def listar_ajustes_por_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin)
):
    return get_ajustes_by_cliente(db, cliente_id)
