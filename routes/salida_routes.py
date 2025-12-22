from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.salida_schema import SalidaCreate, SalidaResponse
from crud import crud_salidas

# 🔒 seguridad
from security import get_current_user
from models.usuario_model import Usuario

router = APIRouter(prefix="/salidas", tags=["Salidas"])


# ======================================================
# 🔒 SOLO ADMIN
# ======================================================
def require_admin(usuario: Usuario = Depends(get_current_user)):
    if usuario.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: solo administradores"
        )
    return usuario


# ======================================================
# ➖ CREAR SALIDA (NO response_model, como antes)
# ======================================================
@router.post("/")
def crear_salida(
    data: SalidaCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin)
):
    return crud_salidas.crear_salida(db, data)


# ======================================================
# 📄 LISTAR SALIDAS POR NIT
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
