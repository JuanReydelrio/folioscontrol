"""
Operaciones CRUD sobre la tabla clientes.
Todas las verificaciones de permisos se hacen en las rutas (routes),
aquí sólo operaciones puras contra la base de datos.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import date

from models.cliente_model import Cliente
from models.resumen_mensual_model import ResumenMensual
from models.resumen_anual_model import ResumenAnual

from schemas.cliente_schema import ClienteCreate, ClienteUpdate


# ======================================================
#                   CREAR CLIENTE
# ======================================================
def create_cliente(db: Session, cliente: ClienteCreate) -> Cliente:
    """
    Crea un nuevo cliente y genera:
    - Resumen anual del año actual
    - Los 12 resúmenes mensuales
    Regla:
    - SOLO el mes actual queda abierto
    - Los demás meses quedan cerrados
    """

    # -------------------------------
    # Validar NIT duplicado
    # -------------------------------
    existente = db.query(Cliente).filter(Cliente.nit == cliente.nit).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un cliente con ese NIT."
        )

    # -------------------------------
    # Crear cliente
    # -------------------------------
    nuevo = Cliente(
        nombre=cliente.nombre,
        nit=cliente.nit,
        saldo_actual=cliente.saldo_actual or 0,
        bloqueado=cliente.bloqueado or False,
        minimo_alerta=cliente.minimo_alerta,
        inactivo=cliente.inactivo or False
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    # -------------------------------
    # Fechas actuales
    # -------------------------------
    hoy = date.today()
    anio_actual = hoy.year
    mes_actual = hoy.month

    try:
        # ==================================================
        # Resumen anual
        # ==================================================
        resumen_anual = ResumenAnual(
            cliente_id=nuevo.id,
            anio=anio_actual,
            total_facturas=0,
            total_notas_credito=0,
            total_notas_debito=0,
            total_documentos_soporte=0,
            total_nomina_electronica=0,
            total_ajuste_nomina=0,
            total_nota_ajuste=0,
            total_entradas=0,
            saldo_final=nuevo.saldo_actual
        )
        db.add(resumen_anual)

        # ==================================================
        # Resúmenes mensuales (12 meses)
        # ==================================================
        for mes in range(1, 13):
            es_mes_actual = mes == mes_actual

            resumen_mensual = ResumenMensual(
                cliente_id=nuevo.id,
                anio=anio_actual,
                mes=mes,
                estado="abierto" if es_mes_actual else "cerrado",
                saldo_inicial=nuevo.saldo_actual if es_mes_actual else 0,
                saldo_final=nuevo.saldo_actual if es_mes_actual else 0,
                total_facturas=0,
                total_notas_credito=0,
                total_notas_debito=0,
                total_documentos_soporte=0,
                total_nomina_electronica=0,
                total_ajuste_nomina=0,
                total_nota_ajuste=0,
                total_entradas=0
            )

            db.add(resumen_mensual)

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creando resúmenes del cliente: {str(e)}"
        )

    return nuevo


# ======================================================
#                   OBTENER
# ======================================================
def get_clientes(db: Session) -> list[Cliente]:
    return db.query(Cliente).all()


def get_cliente_by_id(db: Session, cliente_id: int) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado."
        )
    return cliente


# ======================================================
#                   ACTUALIZAR
# ======================================================
def update_cliente(db: Session, cliente_id: int, datos: ClienteUpdate) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado."
        )

    update_data = datos.dict(exclude_unset=True)

    # Verificar duplicado de NIT
    if "nit" in update_data:
        otro = db.query(Cliente).filter(
            Cliente.nit == update_data["nit"],
            Cliente.id != cliente_id
        ).first()
        if otro:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe otro cliente con ese NIT."
            )

    for key, val in update_data.items():
        setattr(cliente, key, val)

    db.commit()
    db.refresh(cliente)
    return cliente


# ======================================================
#                   ELIMINAR
# ======================================================
def delete_cliente(db: Session, cliente_id: int):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado."
        )

    db.delete(cliente)
    db.commit()

    return {"message": f"Cliente '{cliente.nombre}' eliminado correctamente."}


# ======================================================
#                   ESTADOS
# ======================================================
def toggle_bloqueo_cliente(db: Session, cliente_id: int, bloquear: bool) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado."
        )

    cliente.bloqueado = bloquear
    db.commit()
    db.refresh(cliente)
    return cliente


def toggle_inactivo_cliente(db: Session, cliente_id: int, inactivar: bool) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado."
        )

    cliente.inactivo = inactivar

    # Regla de seguridad
    if inactivar:
        cliente.bloqueado = True

    db.commit()
    db.refresh(cliente)
    return cliente
