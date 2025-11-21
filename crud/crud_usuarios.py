# ============================================
# Módulo: crud_usuarios.py
# Gestión de usuarios:
# - Crear nuevos usuarios
# - Listar usuarios existentes
# - Buscar usuario por nombre
# - Validar credenciales (login)
# ============================================

from sqlalchemy.orm import Session
from models.usuario_model import Usuario
from schemas.usuario_schema import UsuarioCreate, UsuarioLogin, UsuarioResponse
from security import hash_password, verify_password, create_access_token
from datetime import timedelta
from fastapi import HTTPException, status


# 🧩 Crear usuario
def create_usuario(db: Session, usuario: UsuarioCreate):
    # Verificamos si ya existe un usuario con el mismo nombre
    existente = db.query(Usuario).filter(Usuario.nombre_usuario == usuario.nombre_usuario).first()
    if existente:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    # Hasheamos (encriptamos) la contraseña antes de guardarla
    hashed = hash_password(usuario.contrasena)

    nuevo = Usuario(
        nombre_usuario=usuario.nombre_usuario,
        contrasena=hashed,
        rol=usuario.rol
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return nuevo


# 🧩 Listar todos los usuarios
def get_usuarios(db: Session):
    return db.query(Usuario).all()


# 🧩 Buscar usuario por nombre (para login o validaciones)
def get_usuario_by_nombre(db: Session, nombre_usuario: str):
    return db.query(Usuario).filter(Usuario.nombre_usuario == nombre_usuario).first()


# 🧩 Validar login y generar token JWT
def login_usuario(db: Session, credenciales: UsuarioLogin):
    usuario = get_usuario_by_nombre(db, credenciales.nombre_usuario)
    if not usuario:
        raise HTTPException(status_code=400, detail="Usuario no encontrado")

    # Verificamos la contraseña ingresada
    if not verify_password(credenciales.contrasena, usuario.contrasena):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")

    # Generamos token de acceso (válido por 1 hora)
    access_token_expires = timedelta(hours=1)
    token = create_access_token(
        data={"sub": usuario.nombre_usuario, "rol": usuario.rol.value},
        expires_delta=access_token_expires
    )

    return {"access_token": token, "token_type": "bearer"}
