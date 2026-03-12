from fastapi import HTTPException
from models.usuario_model import RolEnum


def validar_acceso_cliente(usuario, cliente_id):

    if usuario.rol != RolEnum.admin:

        if usuario.cliente_id != cliente_id:

            raise HTTPException(
                status_code=403,
                detail="No tiene permiso para acceder a este cliente."
            )
