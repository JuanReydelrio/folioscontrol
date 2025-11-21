# routes/entrada_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas.entrada_schema import EntradaCreate, EntradaUpdate, EntradaResponse
from crud import crud_entradas
from security import get_current_user
from models.usuario_model import Usuario

router = APIRouter(prefix="/entradas", tags=["Entradas"])


# --- Middleware de seguridad ---
def require_admin(usuario: Usuario = Depends(get_current_user)):
    """
    Permite solo a los administradores acceder a las rutas protegidas.
    Se usa en todos los endpoints de entradas.
    """
    if usuario.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: solo administradores pueden realizar esta acción."
        )
    return usuario


# --- Crear entrada ---
@router.post("/", response_model=EntradaResponse, status_code=status.HTTP_201_CREATED)
def crear_entrada(
    entrada: EntradaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)
):
    """
    Crear una nueva entrada de folios.
    • Solo administradores
    • Actualiza el saldo del cliente sumando la cantidad
    """
    return crud_entradas.create_entrada(db, entrada, usuario.id)


# --- Listar entradas ---
@router.get("/", response_model=List[EntradaResponse])
def listar_entradas(
    db: Session = Depends(get_db),
    _ : Usuario = Depends(require_admin)
):
    """
    Obtener todas las entradas registradas.
    • Solo administradores
    """
    return crud_entradas.get_entradas(db)


# --- Obtener una entrada por ID ---
@router.get("/{entrada_id}", response_model=EntradaResponse)
def obtener_entrada(
    entrada_id: int,
    db: Session = Depends(get_db),
    _ : Usuario = Depends(require_admin)
):
    
    """ Obtener una sola entrada por su ID (solo admin) """
    return crud_entradas.get_entrada_by_id(db, entrada_id)

    
@router.get("/cliente/{cliente_id}")
def get_entradas_by_cliente(cliente_id: int, db: Session = Depends(get_db)):
    return crud_entradas.get_entradas_by_cliente(db, cliente_id)


# --- Actualizar entrada ---
@router.put("/{entrada_id}", response_model=EntradaResponse)
def actualizar_entrada(
    entrada_id: int,
    datos: EntradaUpdate,
    db: Session = Depends(get_db),
    _ : Usuario = Depends(require_admin)
):
    """
    Actualizar una entrada existente.
    Y ajustar el saldo del cliente.
    """
    return crud_entradas.update_entrada(db, entrada_id, datos)


# --- Eliminar entrada ---
@router.delete("/{entrada_id}", status_code=status.HTTP_200_OK)
def eliminar_entrada(
    entrada_id: int,
    db: Session = Depends(get_db),
    _ : Usuario = Depends(require_admin)
):
    """
    Eliminar una entrada.
    Restará automáticamente los folios al saldo del cliente.
    """
    return crud_entradas.delete_entrada(db, entrada_id)
