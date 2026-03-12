# routes/clientes_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Union

from database import get_db
from schemas.cliente_schema import ClienteCreate, ClienteUpdate, ClienteResponse, ClienteUsuarioResponse
from crud import crud_clientes
from security import get_current_user  # tu función que devuelve Usuario ORM
from models.usuario_model import RolEnum, Usuario

router = APIRouter(prefix="/clientes", tags=["Clientes"])

#============================
# Función de dependencia para verificar rol admin
#============================
def require_admin(usuario: Usuario = Depends(get_current_user)):

    if usuario.rol != RolEnum.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo para administradores"
        )

    return usuario

#============================
# crud de clientes - solo accesible para admin
#============================

@router.post("/", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def crear_cliente(cliente: ClienteCreate, db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Crear cliente - solo admin"""
    return crud_clientes.create_cliente(db, cliente)

#============================
# Listar clientes
#============================

@router.get("/", response_model=List[Union[ClienteResponse, ClienteUsuarioResponse]])
def listar_clientes(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    """Listar clientes - admin ve todo, usuario normal solo su cliente"""
    if usuario.rol == RolEnum.admin:
        return crud_clientes.get_clientes(db)
    cliente = crud_clientes.get_cliente_by_id(db, usuario.cliente_id)
    return [cliente]

#============================
# obtener cliente por id
#============================

@router.get("/{cliente_id}", response_model=Union[ClienteResponse, ClienteUsuarioResponse])
def obtener_cliente(cliente_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    """Obtener cliente por ID - admin ve todo, usuario normal solo su cliente"""
    cliente = crud_clientes.get_cliente_by_id(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    if usuario.rol == RolEnum.admin:
        return cliente
    elif usuario.cliente_id == cliente_id:
        return cliente
    else:
        raise HTTPException(status_code=403, detail="No autorizado para ver este cliente")
    
#============================
# Actualizar cliente
#============================

@router.put("/{cliente_id}", response_model=ClienteResponse)
def actualizar_cliente(cliente_id: int, datos: ClienteUpdate, db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Actualizar cliente - solo admin"""
    return crud_clientes.update_cliente(db, cliente_id, datos)


@router.delete("/{cliente_id}", status_code=status.HTTP_200_OK)
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db), _ = Depends(require_admin)):
    """Eliminar cliente - solo admin"""
    return crud_clientes.delete_cliente(db, cliente_id)

@router.patch("/{cliente_id}/bloqueo", response_model=ClienteResponse)
def cambiar_estado_bloqueo(
    cliente_id: int,
    bloquear: bool,
    db: Session = Depends(get_db),
    _ = Depends(require_admin)
):
    """
    Bloquear o desbloquear un cliente.
    Parámetro: bloquear=true/false
    """
    return crud_clientes.toggle_bloqueo_cliente(db, cliente_id, bloquear)

# ✅ NUEVO ENDPOINT PARA INACTIVAR / ACTIVAR
@router.patch("/{cliente_id}/inactivo", response_model=ClienteResponse)
def cambiar_estado_inactivo(
    cliente_id: int,
    inactivo: bool,
    db: Session = Depends(get_db),
    _ = Depends(require_admin)
):
    return crud_clientes.toggle_inactivo_cliente(db, cliente_id, inactivo)
