from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

from crud import crud_usuarios
from schemas.usuario_schema import UsuarioCreate, UsuarioLogin, UsuarioResponse

from security import get_current_user
from models.usuario_model import Usuario
from fastapi import HTTPException, status

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)


# ======================================================
# 🔒 DEPENDENCIA: SOLO ADMIN
# ======================================================
def require_admin(usuario: Usuario = Depends(get_current_user)):
    if usuario.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: solo administradores."
        )
    return usuario


# ======================================================
# 🧩 Crear nuevo usuario (SOLO ADMIN)
# ======================================================
@router.post("/", response_model=UsuarioResponse)
def crear_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    _ = Depends(require_admin)
):
    return crud_usuarios.create_usuario(db, usuario)


# ======================================================
# 🧩 Listar usuarios (SOLO ADMIN)
# ======================================================
@router.get("/", response_model=list[UsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    _ = Depends(require_admin)
):
    return crud_usuarios.get_usuarios(db)


# ======================================================
# 🔓 Login (PÚBLICO)
# ======================================================
@router.post("/login")
def login(
    usuario: UsuarioLogin,
    db: Session = Depends(get_db)
):
    return crud_usuarios.login_usuario(db, usuario)
