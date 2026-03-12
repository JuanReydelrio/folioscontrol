# ============================================
# security.py
# Módulo para:
# - Hashear contraseñas
# - Verificar contraseñas
# - Crear tokens JWT
# - Obtener usuario autenticado
# ============================================

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv

from database import get_db
from models.usuario_model import Usuario, RolEnum

# Cargar variables de entorno
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "secret_dev_key")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/usuarios/login")


# ============================================
# HASH PASSWORD
# ============================================

def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])


# ============================================
# VERIFY PASSWORD
# ============================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        plain_password = plain_password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


# ============================================
# CREATE TOKEN
# ============================================

def create_access_token(data: dict, expires_delta: timedelta | None = None):

    to_encode = data.copy()

    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=60))

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


# ============================================
# GET CURRENT USER
# ============================================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username: str = payload.get("sub")
        rol: str = payload.get("rol")
        cliente_id: int | None = payload.get("cliente_id")

        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    usuario = db.query(Usuario).filter(
        Usuario.nombre_usuario == username
    ).first()

    if usuario is None:
        raise credentials_exception

    # 👇 convertir rol string a Enum
    usuario.rol = RolEnum(rol)

    # 👇 asignar cliente al usuario
    usuario.cliente_id = cliente_id

    return usuario


# ============================================
# SOLO ADMIN
# ============================================

def require_admin(
    current_user: Usuario = Depends(get_current_user)
):

    if current_user.rol != RolEnum.admin:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: solo administradores pueden realizar esta acción."
        )

    return current_user