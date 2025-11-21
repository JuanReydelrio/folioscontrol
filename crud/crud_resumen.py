# crud/crud_resumen.py
from sqlalchemy.orm import Session
from models.resumen_mensual_model import ResumenMensual
from models.resumen_anual_model import ResumenAnual
from models.cliente_model import Cliente
from datetime import datetime, date

# ------------------------------------------
# UTILIDAD: Obtener o crear resumen mensual
# ------------------------------------------
def get_or_create_resumen_mensual(db: Session, cliente_id: int, anio: int, mes: int):
    resumen = (
        db.query(ResumenMensual)
        .filter_by(cliente_id=cliente_id, anio=anio, mes=mes)
        .first()
    )

    if resumen is None:
        resumen = ResumenMensual(
            cliente_id=cliente_id,
            anio=anio,
            mes=mes,
            total_facturas=0,
            total_notas_credito=0,
            total_notas_debito=0,
            total_documentos_soporte=0,
            total_nomina_electronica=0,
            total_ajuste_nomina=0,
            total_nota_ajuste=0,
            total_entradas=0,
            saldo_final=0,
        )
        db.add(resumen)
        db.commit()
        db.refresh(resumen)

    return resumen
def recalcular_saldo_resumenes(db: Session, cliente_id: int, anio: int, mes: int):

    resumen_m = db.query(ResumenMensual).filter_by(
        cliente_id=cliente_id, anio=anio, mes=mes
    ).first()

    if resumen_m:
        resumen_m.saldo_final = (
            (resumen_m.total_entradas or 0)
            - (
                (resumen_m.total_facturas or 0)
                + (resumen_m.total_notas_credito or 0)
                + (resumen_m.total_notas_debito or 0)
                + (resumen_m.total_documentos_soporte or 0)
                + (resumen_m.total_nomina_electronica or 0)
                + (resumen_m.total_ajuste_nomina or 0)
                + (resumen_m.total_nota_ajuste or 0)
            )
        )
        db.add(resumen_m)

    resumen_a = db.query(ResumenAnual).filter_by(
        cliente_id=cliente_id, anio=anio
    ).first()

    if resumen_a:
        resumen_a.saldo_final = (
            (resumen_a.total_entradas or 0)
            - (
                (resumen_a.total_facturas or 0)
                + (resumen_a.total_notas_credito or 0)
                + (resumen_a.total_notas_debito or 0)
                + (resumen_a.total_documentos_soporte or 0)
                + (resumen_a.total_nomina_electronica or 0)
                + (resumen_a.total_ajuste_nomina or 0)
                + (resumen_a.total_nota_ajuste or 0)
            )
        )

        db.add(resumen_a)

    db.commit()


# ------------------------------------------
# UTILIDAD: Obtener o crear resumen anual
# ------------------------------------------
def get_or_create_resumen_anual(db: Session, cliente_id: int, anio: int):
    resumen = (
        db.query(ResumenAnual)
        .filter_by(cliente_id=cliente_id, anio=anio)
        .first()
    )

    if resumen is None:
        resumen = ResumenAnual(
            cliente_id=cliente_id,
            anio=anio,
            total_facturas=0,
            total_notas_credito=0,
            total_notas_debito=0,
            total_documentos_soporte=0,
            total_nomina_electronica=0,
            total_ajuste_nomina=0,
            total_nota_ajuste=0,
            total_entradas=0,
            saldo_final=0,
        )
        db.add(resumen)
        db.commit()
        db.refresh(resumen)

    return resumen


# ------------------------------------------
# SUMAR ENTRADAS (cuando admin carga folios)
# ahora recibe `fecha` para determinar mes/anio correctos
# ------------------------------------------
def sumar_entrada(db: Session, cliente_id: int, cantidad: int, fecha: date):
    anio = fecha.year
    mes = fecha.month

    # Obtener o crear resúmenes
    resumen_m = get_or_create_resumen_mensual(db, cliente_id, anio, mes)
    resumen_a = get_or_create_resumen_anual(db, cliente_id, anio)

    # Sumamos entradas (NO facturas)
    resumen_m.total_entradas = (resumen_m.total_entradas or 0) + cantidad
    resumen_a.total_entradas = (resumen_a.total_entradas or 0) + cantidad

    db.add(resumen_m)
    db.add(resumen_a)
    db.commit()

    recalcular_saldo_resumenes(db, cliente_id, anio, mes)

    return resumen_m, resumen_a



def restar_entrada(db: Session, cliente_id: int, cantidad: int, fecha: date):
    anio = fecha.year
    mes = fecha.month

    resumen_m = db.query(ResumenMensual).filter_by(
        cliente_id=cliente_id, anio=anio, mes=mes
    ).first()

    resumen_a = db.query(ResumenAnual).filter_by(
        cliente_id=cliente_id, anio=anio
    ).first()

    if not resumen_m or not resumen_a:
        return

    # Restar entradas, con piso en 0
    resumen_m.total_entradas = max((resumen_m.total_entradas or 0) - cantidad, 0)
    resumen_a.total_entradas = max((resumen_a.total_entradas or 0) - cantidad, 0)

    db.add(resumen_m)
    db.add(resumen_a)
    db.commit()

    recalcular_saldo_resumenes(db, cliente_id, anio, mes)

    return resumen_m, resumen_a


# ------------------------------------------
# SUMAR SALIDAS (FACTURA / NC / ND / DS / ...)
# ahora recibe `fecha` para usar mes/anio de la operación
# ------------------------------------------
def sumar_salida(db: Session, cliente_id: int, tipo_documento: str, fecha: date):
    if fecha is None:
        hoy = datetime.now()
        anio = hoy.year
        mes = hoy.month
    else:
        if isinstance(fecha, datetime):
            anio = fecha.year
            mes = fecha.month
        else:
            anio = fecha.year
            mes = fecha.month

    mensual = get_or_create_resumen_mensual(db, cliente_id, anio, mes)
    anual = get_or_create_resumen_anual(db, cliente_id, anio)

    # ---- Sumar según el tipo ----
    if tipo_documento == "FACTURA":
        mensual.total_facturas = (mensual.total_facturas or 0) + 1
        anual.total_facturas = (anual.total_facturas or 0) + 1

    elif tipo_documento == "NOTA_CREDITO":
        mensual.total_notas_credito = (mensual.total_notas_credito or 0) + 1
        anual.total_notas_credito = (anual.total_notas_credito or 0) + 1

    elif tipo_documento == "NOTA_DEBITO":
        mensual.total_notas_debito = (mensual.total_notas_debito or 0) + 1
        anual.total_notas_debito = (anual.total_notas_debito or 0) + 1

    elif tipo_documento == "DOCUMENTO_SOPORTE":
        mensual.total_documentos_soporte = (mensual.total_documentos_soporte or 0) + 1
        anual.total_documentos_soporte = (anual.total_documentos_soporte or 0) + 1

    elif tipo_documento == "NOMINA_ELECTRONICA":
        mensual.total_nomina_electronica = (mensual.total_nomina_electronica or 0) + 1
        anual.total_nomina_electronica = (anual.total_nomina_electronica or 0) + 1

    elif tipo_documento == "AJUSTE_NOMINA":
        mensual.total_ajuste_nomina = (mensual.total_ajuste_nomina or 0) + 1
        anual.total_ajuste_nomina = (anual.total_ajuste_nomina or 0) + 1

    elif tipo_documento == "NOTA_AJUSTE":
        mensual.total_nota_ajuste = (mensual.total_nota_ajuste or 0) + 1
        anual.total_nota_ajuste = (anual.total_nota_ajuste or 0) + 1

    else:
        raise ValueError(f"Tipo de documento desconocido: {tipo_documento}")

    db.commit()
    db.refresh(mensual)
    db.refresh(anual)

    return mensual, anual


# ------------------------------------------
# CIERRE DE MES: Guardar saldo_final
# ------------------------------------------
def cerrar_mes(db: Session, cliente_id: int, anio: int, mes: int):
    cliente = db.query(Cliente).filter_by(id=cliente_id).first()
    if not cliente:
        return None

    resumen = get_or_create_resumen_mensual(db, cliente_id, anio, mes)
    resumen.saldo_final = cliente.saldo_actual

    db.commit()
    return resumen


# ------------------------------------------
# CIERRE DE AÑO
# ------------------------------------------
def cerrar_anio(db: Session, cliente_id: int, anio: int):
    cliente = db.query(Cliente).filter_by(id=cliente_id).first()
    if not cliente:
        return None

    resumen = get_or_create_resumen_anual(db, cliente_id, anio)
    resumen.saldo_final = cliente.saldo_actual

    db.commit()
    return resumen


# ======================================================
#               CONSULTAS POR NIT
# ======================================================

# --- Obtener resumen mensual por NIT ---
def resumen_mensual_por_nit(db: Session, nit: str, anio: int, mes: int):
    return (
        db.query(ResumenMensual)
        .join(Cliente)
        .filter(Cliente.nit == nit, ResumenMensual.anio == anio, ResumenMensual.mes == mes)
        .first()
    )


# --- Obtener resumen anual por NIT ---
def resumen_anual_por_nit(db: Session, nit: str, anio: int):
    return (
        db.query(ResumenAnual)
        .join(Cliente)
        .filter(Cliente.nit == nit, ResumenAnual.anio == anio)
        .first()
    )

