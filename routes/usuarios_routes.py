# Este módulo define las rutas (endpoints) del API relacionadas con usuarios.
# Aquí conectamos las funciones CRUD con las rutas HTTP.
# 
# - POST /usuarios/ → Crear nuevo usuario
# - GET /usuarios/ → Listar todos los usuarios
# - POST /usuarios/login → Iniciar sesión (login)
#
# Cada ruta se comunica con crud_usuarios.py para ejecutar la lógica de negocio.

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from crud import crud_usuarios
from schemas.usuario_schema import UsuarioCreate, UsuarioLogin, UsuarioResponse

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)

# 🧩 Crear nuevo usuario
@router.post("/", response_model=UsuarioResponse)
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    return crud_usuarios.create_usuario(db, usuario)


# 🧩 Listar todos los usuarios
@router.get("/", response_model=list[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    return crud_usuarios.get_usuarios(db)


# 🧩 Login de usuario (genera token)
@router.post("/login")
def login(usuario: UsuarioLogin, db: Session = Depends(get_db)):
    return crud_usuarios.login_usuario(db, usuario)
