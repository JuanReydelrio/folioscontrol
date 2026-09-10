#crud/crud_salidas.py
from sqlalchemy.orm import Session
from models.salida_model import Salida
from models.cliente_model import Cliente
from schemas.salida_schema import SalidaCreate
from services.time_service import obtener_fecha_actual
from services.email_service import enviar_alerta_folios   
import time
from crud.crud_resumen import sumar_salida, cierre_mensual_automatico, validar_mes_abierto, verificar_cambio_anio

# ======================================================
# 🔔 ALERTAS CONTROLADAS (SIN SPAM)
# ======================================================
def verificar_y_enviar_alerta(cliente, saldo_antes, saldo_despues, mensaje):
    # 🟡 Cruza mínimo de alerta
    if (
        saldo_antes > cliente.minimo_alerta
        and saldo_despues <= cliente.minimo_alerta
        and saldo_despues > 0
    ):
        enviar_alerta_folios(
            cliente_nombre=cliente.nombre,
            nit=cliente.nit,
            mensaje=mensaje,
            saldo=saldo_despues
        )

    # 🔴 Llega a 0
    if saldo_antes > 0 and saldo_despues == 0:
        enviar_alerta_folios(
            cliente_nombre=cliente.nombre,
            nit=cliente.nit,
            mensaje=mensaje,
            saldo=saldo_despues
        )


def crear_salida(db: Session, data: SalidaCreate):
    tiempo_total= time.pref_counter()

    hoy = obtener_fecha_actual()

    inicio = time.perf_counter()

    # 2. Buscar cliente por NIT
    cliente: Cliente | None = db.query(Cliente).filter(Cliente.nit == data.nit).first()
    print(f"[TIEMPO] Buscar cliente: {time.perf_counter() - inicio:.3f} s")
    
    if not cliente:
        return {"estado": "RECHAZADO", "mensaje": "El cliente no existe."}

    # 3. Cliente inactivo
    if cliente.inactivo:
        return {
            "estado": "RECHAZADO",
            "mensaje": "El cliente está inactivo y no puede emitir documentos."
        }

    # 4. FLUJO: cierre_mensual_automatico -> verificar_cambio_anio -> abrir mes actual
    verificar_cambio_anio(db, hoy)
    print(f"[TIEMPO] Verificar cambio de año: {time.perf_counter() - inicio:.3f} s")
    cierre_mensual_automatico(db, cliente.id, hoy)
    print(f"[TIEMPO] Cierre mensual automático: {time.perf_counter() - inicio:.3f} s")
    validar_mes_abierto(db, cliente.id, hoy)
    print(f"[TIEMPO] Validar mes abierto: {time.perf_counter() - inicio:.3f} s")


    cantidad = 1

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
    print(f"[TIEMPO] Verificar duplicado: {time.perf_counter() - inicio:.3f} s")

    if duplicado:
        return {
            "estado": "APROBADO",
            "mensaje": "Documento duplicado. No se descontó folio."
        }
    saldo_antes = cliente.saldo_actual
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
            fecha_documento=hoy,
            cantidad=cantidad
        )

        db.add(nueva_salida)
        cliente.saldo_actual = saldo_despues
        # 🔥 Actualiza resumen mensual + anual
        sumar_salida(db, cliente.id, data.tipo_documento, hoy)
        print(f"[TIEMPO] Registrar salida: {time.perf_counter() - inicio:.3f} s")
        db.commit()
        print(f"[TIEMPO] Commit: {time.perf_counter() - inicio:.3f} s")
        db.refresh(nueva_salida) 
        db.refresh(cliente)
# === NUEVA LÓGICA: También usar APROBADO/FINALIZANDO para bloqueados ===
        if saldo_despues <= cliente.minimo_alerta:
            if saldo_despues > 0:
                mensaje = f"Folios restantes: {saldo_despues}. Se recomienda adquirir más folios."
            else:
                mensaje = "Ya no te quedan folios disponibles. Contacte a su proveedor."
            estado_final = "APROBADO/FINALIZANDO"
        else:
            mensaje = "Operación aprobada."
            estado_final = "APROBADO"

        return {"estado": estado_final, "mensaje": mensaje}
    
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
        fecha_documento=hoy,
        cantidad=cantidad
    )

    db.add(nueva_salida)
    cliente.saldo_actual = saldo_despues
    # 🔥 Actualizar resumen mensual + anual
    sumar_salida(db, cliente.id, data.tipo_documento, hoy)
    
    db.commit()
    db.refresh(nueva_salida)
    db.refresh(cliente)

    verificar_y_enviar_alerta(
        cliente,
        saldo_antes,
        saldo_despues,
        mensaje
    )
# Cambio principal: decidir estado final según si está en o por debajo del mínimo
    estado_final = "APROBADO"
    if saldo_despues <= cliente.minimo_alerta:
        estado_final = "APROBADO/FINALIZANDO"


    return {"estado": estado_final, "mensaje": mensaje}

def obtener_salidas_por_nit(db: Session, nit: str):
    cliente = db.query(Cliente).filter(Cliente.nit == nit).first()

    if not cliente:
        return None

    salidas = db.query(Salida).filter(Salida.cliente_id == cliente.id).all()
    return salidas