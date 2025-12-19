#crud/crud_salidas.py
from sqlalchemy.orm import Session
from models.salida_model import Salida
from models.cliente_model import Cliente
from schemas.salida_schema import SalidaCreate
from datetime import date
from crud.crud_resumen import sumar_salida



def crear_salida(db: Session, data: SalidaCreate):

    cantidad = 1
    hoy = date.today()

    cliente: Cliente = db.query(Cliente).filter(Cliente.nit == data.nit).first()

    if not cliente:
        return {"estado": "RECHAZADO", "mensaje": "El cliente no existe."}

    # Cliente inactivo
    if cliente.inactivo:
        return {
            "estado": "RECHAZADO",
            "mensaje": "El cliente está inactivo y no puede emitir documentos."
        }

    # Duplicado
    duplicado = db.query(Salida).filter(
        Salida.cliente_id == cliente.id,
        Salida.tipo_documento == data.tipo_documento,
        Salida.numero_documento == data.numero_documento
    ).first()

    if duplicado:
        return {
            "estado": "APROBADO",
            "mensaje": "Documento duplicado. No se descontó folio."
        }

    saldo_despues = cliente.saldo_actual - cantidad

    # ====================================
    # 4. CLIENTE BLOQUEADO
    # ====================================
    if cliente.bloqueado:

        if cliente.saldo_actual <= 0:
            return {
                "estado": "RECHAZADO",
                "mensaje": "Cliente sin folios disponibles, Porfavor contactese con DREAMSOFT para adquirir más folios."
            }

        # Bloqueado pero queda en mínimo de alerta
        if saldo_despues <= cliente.minimo_alerta:
            mensaje = f"Folios restantes: {saldo_despues}. Se recomienda adquirir más folios."

        # Bloqueado y operación normal
        else:
            mensaje = f"Operación aprobada."

        # Registrar salida
        nueva_salida = Salida(
            cliente_id=cliente.id,
            tipo_documento=data.tipo_documento,
            numero_documento=data.numero_documento,
            fecha_documento=date.today(),
            cantidad=cantidad
        )

        db.add(nueva_salida)
        cliente.saldo_actual = saldo_despues
        db.commit()
        db.refresh(nueva_salida) 
        # 🔥 Actualiza resumen mensual + anual
        sumar_salida(db, cliente.id, data.tipo_documento, hoy)
        return {"estado": "APROBADO", "mensaje": mensaje}

    # ====================================
    # 5. CLIENTE NO BLOQUEADO
    # ====================================

    # Caso → saldo suficiente y sobra
    if cliente.saldo_actual > cantidad:

        saldo_despues = cliente.saldo_actual - cantidad

        # Caso queda en 0 EXACTO
        if saldo_despues == 0:
            mensaje = "Ya no te quedan folios disponibles. Contacte a su proveedor."

        # Caso dentro de mínimo de alerta
        elif saldo_despues <= cliente.minimo_alerta:
            mensaje = f"Folios restantes: {saldo_despues}. Se recomienda adquirir más folios."

        else:
            mensaje = "Operación aprobada."

    # Caso → saldo exacto al consumo (1 → queda en 0)
    elif cliente.saldo_actual == cantidad:
        saldo_despues = 0
        mensaje = "Ya no te quedan folios disponibles. Contacte a su proveedor."

    # Caso → saldo insuficiente → saldo negativo permitido
    else:
        saldo_despues = cliente.saldo_actual - cantidad
        mensaje = f"Saldo insuficiente. Su saldo es negativo ({saldo_despues}). Contacte a su proveedor."

    # Registrar salida
    nueva_salida = Salida(
        cliente_id=cliente.id,
        tipo_documento=data.tipo_documento,
        numero_documento=data.numero_documento,
        fecha_documento=date.today(),
        cantidad=cantidad
    )

    db.add(nueva_salida)
    cliente.saldo_actual = saldo_despues
    db.commit()
    db.refresh(nueva_salida)
    db.refresh(cliente)
        # 🔥 Actualizar resumen mensual + anual
    sumar_salida(db, cliente.id, data.tipo_documento, hoy)

    return {"estado": "APROBADO", "mensaje": mensaje}

def obtener_salidas_por_nit(db: Session, nit: str):
    cliente = db.query(Cliente).filter(Cliente.nit == nit).first()

    if not cliente:
        return None

    salidas = db.query(Salida).filter(Salida.cliente_id == cliente.id).all()
    return salidas