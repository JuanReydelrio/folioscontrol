from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas.entrada_schema import EntradaCreate, EntradaUpdate, EntradaResponse
from crud import crud_entradas
from security import get_current_user
from models.usuario_model import Usuario, RolEnum

router = APIRouter(
    prefix="/entradas",
    tags=["Entradas"]
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
# ➕ CREAR ENTRADA
# ======================================================
@router.post(
    "/",
    response_model=EntradaResponse,
    status_code=status.HTTP_201_CREATED
)
def crear_entrada(
    entrada: EntradaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)
):
    """
    Crear una nueva entrada de folios.

    • Solo administradores
    • Actualiza el saldo del cliente
    """

    return crud_entradas.create_entrada(db, entrada, usuario.id)


# ======================================================
# 📄 LISTAR TODAS LAS ENTRADAS
# ======================================================
@router.get(
    "/",
    response_model=List[EntradaResponse]
)
def listar_entradas(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin)
):
    """
    Obtener todas las entradas registradas.

    • Solo administradores
    """

    return crud_entradas.get_entradas(db)


# ======================================================
# 🔍 OBTENER ENTRADA POR ID
# ======================================================
@router.get(
    "/{entrada_id}",
    response_model=EntradaResponse
)
def obtener_entrada(
    entrada_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin)
):
    """
    Obtener una entrada por su ID.

    • Solo administradores
    """

    entrada = crud_entradas.get_entrada_by_id(db, entrada_id)

    if not entrada:
        raise HTTPException(
            status_code=404,
            detail="Entrada no encontrada"
        )

    return entrada


# ======================================================
# 📄 ENTRADAS POR CLIENTE
# ======================================================
@router.get(
    "/cliente/{cliente_id}",
    response_model=List[EntradaResponse]
)
def get_entradas_by_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    """
    Obtener entradas de un cliente.

    • Admin → puede ver cualquier cliente
    • Usuario → solo su cliente
    """

    if usuario.rol != RolEnum.admin and usuario.cliente_id != cliente_id:
        raise HTTPException(
            status_code=403,
            detail="No autorizado para ver entradas de este cliente"
        )

    return crud_entradas.get_entradas_by_cliente(db, cliente_id)


# ======================================================
# ✏️ ACTUALIZAR ENTRADA
# ======================================================
@router.put(
    "/{entrada_id}",
    response_model=EntradaResponse
)
def actualizar_entrada(
    entrada_id: int,
    datos: EntradaUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin)
):
    """
    Actualizar una entrada existente.

    • Solo administradores
    """

    return crud_entradas.update_entrada(db, entrada_id, datos)


# ======================================================
# ❌ ELIMINAR ENTRADA
# ======================================================
@router.delete(
    "/{entrada_id}",
    status_code=status.HTTP_200_OK
)
def eliminar_entrada(
    entrada_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin)
):
    """
    Eliminar una entrada.

    • Solo administradores
    """

    return crud_entradas.delete_entrada(db, entrada_id)