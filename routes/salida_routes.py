# routes/salida_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.salida_schema import SalidaCreate, SalidaResponse
from crud import crud_salidas

from security import get_current_user
from models.usuario_model import Usuario, RolEnum
from models.cliente_model import Cliente

from schemas.salida_schema import (
    SalidaCreate,
    SalidaResponse,
    SalidaOperacionResponse
)
router = APIRouter(
    prefix="/salidas",
    tags=["Salidas"]
)

# ======================================================
# 🔒 SOLO ADMIN
# ======================================================
def require_admin(usuario: Usuario = Depends(get_current_user)):
    if usuario.rol != RolEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: solo administradores pueden realizar esta acción."
        )
    return usuario


# ======================================================
# ➖ Crear salida (ADMIN + usuario normal con cliente activo)
# ======================================================
@router.post("/", response_model=SalidaOperacionResponse)
def crear_salida(
    data: SalidaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    # ADMIN → puede usar cualquier NIT
    if usuario.rol == RolEnum.admin:

        return crud_salidas.crear_salida(db, data)

    # ======================================
    # USUARIO NORMAL
    # ======================================

    # obtener su cliente
    cliente = db.query(Cliente).filter(
        Cliente.id == usuario.cliente_id
    ).first()

    if not cliente:

        raise HTTPException(
            status_code=404,
            detail="Cliente del usuario no encontrado"
        )

    # ⚡ FORZAR NIT
    data.nit = cliente.nit

    return crud_salidas.crear_salida(db, data)



# ======================================================
# 📄 Listar salidas por NIT (ADMIN)
# ======================================================
@router.get("/{nit}", response_model=list[SalidaResponse])
def listar_salidas_por_nit(
    nit: str,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin)
):
    salidas = crud_salidas.obtener_salidas_por_nit(db, nit)

    if salidas is None:
        raise HTTPException(
            status_code=404,
            detail="El cliente no existe."
        )

    return salidas

