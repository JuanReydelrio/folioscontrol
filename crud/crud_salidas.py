#crud/crud_salidas.py
from sqlalchemy.orm import Session
from models.salida_model import Salida
from models.cliente_model import Cliente
from schemas.salida_schema import SalidaCreate
from services.time_service import obtener_fecha_actual
from services.email_service import enviar_alerta_folios   
import time
from crud.crud_resumen import sumar_salida, cierre_mensual_automatico, validar_mes_abierto, verificar_cambio_anio_cliente

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

    tiempo_total = time.perf_counter()

    hoy = obtener_fecha_actual()

    # ==================================================
    # 1. BUSCAR CLIENTE POR NIT
    # ==================================================

    inicio = time.perf_counter()

    cliente: Cliente | None = db.query(Cliente).filter(
        Cliente.nit == data.nit
    ).first()

    print(
        f"[TIEMPO] Buscar cliente: "
        f"{time.perf_counter() - inicio:.3f} s"
    )

    if not cliente:
        return {
            "estado": "RECHAZADO",
            "mensaje": "El cliente no existe."
        }

    # ==================================================
    # 2. CLIENTE INACTIVO
    # ==================================================

    if cliente.inactivo:
        return {
            "estado": "RECHAZADO",
            "mensaje": "El cliente está inactivo y no puede emitir documentos."
        }

    # ==================================================
    # 3. VERIFICAR AÑO SOLO PARA ESTE CLIENTE
    # ==================================================

    inicio = time.perf_counter()

    verificar_cambio_anio_cliente(
        db,
        cliente.id,
        hoy
    )

    print(
        f"[TIEMPO] Verificar cambio de año cliente: "
        f"{time.perf_counter() - inicio:.3f} s"
    )

    # ==================================================
    # 4. CIERRE MENSUAL AUTOMÁTICO
    # ==================================================

    inicio = time.perf_counter()

    cierre_mensual_automatico(
        db,
        cliente.id,
        hoy
    )

    print(
        f"[TIEMPO] Cierre mensual automático: "
        f"{time.perf_counter() - inicio:.3f} s"
    )

    # ==================================================
    # 5. VALIDAR MES ABIERTO
    # ==================================================

    inicio = time.perf_counter()

    validar_mes_abierto(
        db,
        cliente.id,
        hoy
    )

    print(
        f"[TIEMPO] Validar mes abierto: "
        f"{time.perf_counter() - inicio:.3f} s"
    )

    cantidad = 1

    # ==================================================
    # 6. VERIFICAR DUPLICADO
    # ==================================================

    inicio = time.perf_counter()

    duplicado = db.query(Salida).filter(
        Salida.cliente_id == cliente.id,
        Salida.tipo_documento == data.tipo_documento,
        Salida.numero_documento == data.numero_documento
    ).first()

    print(
        f"[TIEMPO] Verificar duplicado: "
        f"{time.perf_counter() - inicio:.3f} s"
    )

    if duplicado:
        return {
            "estado": "APROBADO",
            "mensaje": "Documento duplicado. No se descontó folio."
        }

    # ==================================================
    # 7. CALCULAR SALDO
    # ==================================================

    saldo_antes = cliente.saldo_actual
    saldo_despues = cliente.saldo_actual - cantidad

    # ==================================================
    # 8. CLIENTE BLOQUEADO
    # ==================================================

    if cliente.bloqueado:

        if cliente.saldo_actual <= 0:
            return {
                "estado": "RECHAZADO",
                "mensaje": "Cliente sin folios disponibles, Porfavor contactese con DREAMSOFT para adquirir más folios."
            }

        # ----------------------------------------------
        # Mensaje inicial
        # ----------------------------------------------

        if saldo_despues <= cliente.minimo_alerta:
            mensaje = (
                f"Folios restantes: {saldo_despues}. "
                f"Se recomienda adquirir más folios."
            )
        else:
            mensaje = "Operación aprobada."

        # ----------------------------------------------
        # Registrar salida
        # ----------------------------------------------

        nueva_salida = Salida(
            cliente_id=cliente.id,
            tipo_documento=data.tipo_documento,
            numero_documento=data.numero_documento,
            fecha_documento=hoy,
            cantidad=cantidad
        )

        db.add(nueva_salida)

        cliente.saldo_actual = saldo_despues

        # ----------------------------------------------
        # Actualizar resumen mensual + anual
        # ----------------------------------------------

        inicio = time.perf_counter()

        sumar_salida(
            db,
            cliente.id,
            data.tipo_documento,
            hoy
        )

        print(
            f"[TIEMPO] Sumar salida: "
            f"{time.perf_counter() - inicio:.3f} s"
        )

        # ----------------------------------------------
        # Commit
        # ----------------------------------------------

        inicio = time.perf_counter()

        db.commit()

        print(
            f"[TIEMPO] Commit: "
            f"{time.perf_counter() - inicio:.3f} s"
        )

        db.refresh(nueva_salida)
        db.refresh(cliente)

        # ----------------------------------------------
        # Estado final
        # ----------------------------------------------

        if saldo_despues <= cliente.minimo_alerta:

            if saldo_despues > 0:
                mensaje = (
                    f"Folios restantes: {saldo_despues}. "
                    f"Se recomienda adquirir más folios."
                )
            else:
                mensaje = (
                    "Ya no te quedan folios disponibles. "
                    "Contacte a su proveedor."
                )

            estado_final = "APROBADO/FINALIZANDO"

        else:
            mensaje = "Operación aprobada."
            estado_final = "APROBADO"

        print(
            f"[TIEMPO] TOTAL crear_salida: "
            f"{time.perf_counter() - tiempo_total:.3f} s"
        )

        return {
            "estado": estado_final,
            "mensaje": mensaje
        }

    # ==================================================
    # 9. CLIENTE NO BLOQUEADO
    # ==================================================

    # ----------------------------------------------
    # Saldo suficiente y sobra
    # ----------------------------------------------

    if cliente.saldo_actual > cantidad:

        saldo_despues = cliente.saldo_actual - cantidad

        # Queda en 0
        if saldo_despues == 0:

            mensaje = (
                "Ya no te quedan folios disponibles. "
                "Contacte a su proveedor."
            )

        # Dentro del mínimo de alerta
        elif saldo_despues <= cliente.minimo_alerta:

            mensaje = (
                f"Folios restantes: {saldo_despues}. "
                f"Se recomienda adquirir más folios."
            )

        else:

            mensaje = "Operación aprobada."

    # ----------------------------------------------
    # Saldo exacto
    # ----------------------------------------------

    elif cliente.saldo_actual == cantidad:

        saldo_despues = 0

        mensaje = (
            "Ya no te quedan folios disponibles. "
            "Contacte a su proveedor."
        )

    # ----------------------------------------------
    # Saldo insuficiente
    # ----------------------------------------------

    else:

        saldo_despues = cliente.saldo_actual - cantidad

        mensaje = (
            f"Saldo insuficiente. "
            f"Su saldo es negativo ({saldo_despues}). "
            f"Contacte a su proveedor."
        )

    # ==================================================
    # 10. REGISTRAR SALIDA
    # ==================================================

    nueva_salida = Salida(
        cliente_id=cliente.id,
        tipo_documento=data.tipo_documento,
        numero_documento=data.numero_documento,
        fecha_documento=hoy,
        cantidad=cantidad
    )

    db.add(nueva_salida)

    cliente.saldo_actual = saldo_despues

    # ==================================================
    # 11. ACTUALIZAR RESUMEN MENSUAL + ANUAL
    # ==================================================

    inicio = time.perf_counter()

    sumar_salida(
        db,
        cliente.id,
        data.tipo_documento,
        hoy
    )

    print(
        f"[TIEMPO] Sumar salida: "
        f"{time.perf_counter() - inicio:.3f} s"
    )

    # ==================================================
    # 12. COMMIT
    # ==================================================

    inicio = time.perf_counter()

    db.commit()

    print(
        f"[TIEMPO] Commit: "
        f"{time.perf_counter() - inicio:.3f} s"
    )

    db.refresh(nueva_salida)
    db.refresh(cliente)

    # ==================================================
    # 13. VERIFICAR / ENVIAR ALERTA
    # ==================================================

    inicio = time.perf_counter()

    verificar_y_enviar_alerta(
        cliente,
        saldo_antes,
        saldo_despues,
        mensaje
    )

    print(
        f"[TIEMPO] Alerta: "
        f"{time.perf_counter() - inicio:.3f} s"
    )

    # ==================================================
    # 14. ESTADO FINAL
    # ==================================================

    estado_final = "APROBADO"

    if saldo_despues <= cliente.minimo_alerta:
        estado_final = "APROBADO/FINALIZANDO"

    # ==================================================
    # 15. TIEMPO TOTAL
    # ==================================================

    print(
        f"[TIEMPO] TOTAL crear_salida: "
        f"{time.perf_counter() - tiempo_total:.3f} s"
    )

    return {
        "estado": estado_final,
        "mensaje": mensaje
    }

def obtener_salidas_por_nit(db: Session, nit: str):
    cliente = db.query(Cliente).filter(Cliente.nit == nit).first()

    if not cliente:
        return None

    salidas = db.query(Salida).filter(Salida.cliente_id == cliente.id).all()
    return salidas