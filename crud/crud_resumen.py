from sqlalchemy.orm import Session
from datetime import date, datetime
from fastapi import HTTPException, status

from models.resumen_mensual_model import ResumenMensual
from models.resumen_anual_model import ResumenAnual
from models.cliente_model import Cliente


# ======================================================
# 🔁 REFLEJAR SALDO ACTUAL (NO RECALCULA)
# ======================================================
def recalcular_saldo_resumenes(db: Session, cliente_id: int, anio: int, mes: int):

    cliente = db.query(Cliente).filter_by(id=cliente_id).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    resumen_m = db.query(ResumenMensual).filter_by(
        cliente_id=cliente_id, anio=anio, mes=mes
    ).first()

    resumen_a = db.query(ResumenAnual).filter_by(
        cliente_id=cliente_id, anio=anio
    ).first()

    if not resumen_m or not resumen_a:
        raise HTTPException(409, "Resumen inconsistente")

    # 🔒 No tocar meses cerrados
    if resumen_m.estado == "cerrado":
        return

    resumen_m.saldo_final = cliente.saldo_actual
    resumen_a.saldo_final = cliente.saldo_actual

    db.commit()


# ======================================================
# ➕ ENTRADAS
# ======================================================
def sumar_entrada(db: Session, cliente_id: int, cantidad: int, fecha: date):

    anio, mes = fecha.year, fecha.month

    resumen_m = db.query(ResumenMensual).filter_by(
        cliente_id=cliente_id, anio=anio, mes=mes
    ).first()

    resumen_a = db.query(ResumenAnual).filter_by(
        cliente_id=cliente_id, anio=anio
    ).first()

    if not resumen_m or not resumen_a:
        raise HTTPException(409, "No existe resumen del período")

    resumen_m.total_entradas += cantidad
    resumen_a.total_entradas += cantidad

    db.commit()
    recalcular_saldo_resumenes(db, cliente_id, anio, mes)


def restar_entrada(db: Session, cliente_id: int, cantidad: int, fecha: date):

    anio, mes = fecha.year, fecha.month

    resumen_m = db.query(ResumenMensual).filter_by(
        cliente_id=cliente_id, anio=anio, mes=mes
    ).first()

    resumen_a = db.query(ResumenAnual).filter_by(
        cliente_id=cliente_id, anio=anio
    ).first()

    if not resumen_m or not resumen_a:
        raise HTTPException(409, "No existe resumen del período")

    resumen_m.total_entradas = max(resumen_m.total_entradas - cantidad, 0)
    resumen_a.total_entradas = max(resumen_a.total_entradas - cantidad, 0)

    db.commit()
    recalcular_saldo_resumenes(db, cliente_id, anio, mes)


# ======================================================
# ➖ SALIDAS (DOCUMENTOS)
# ======================================================
def sumar_salida(db: Session, cliente_id: int, tipo: str, fecha: date | None):

    fecha = fecha or datetime.now().date()
    anio, mes = fecha.year, fecha.month

    m = db.query(ResumenMensual).filter_by(
        cliente_id=cliente_id, anio=anio, mes=mes
    ).first()

    a = db.query(ResumenAnual).filter_by(
        cliente_id=cliente_id, anio=anio
    ).first()

    if not m or not a:
        raise HTTPException(409, "No existe resumen del período")

    mapa = {
        "FACTURA": "total_facturas",
        "NOTA_CREDITO": "total_notas_credito",
        "NOTA_DEBITO": "total_notas_debito",
        "DOCUMENTO_SOPORTE": "total_documentos_soporte",
        "NOMINA_ELECTRONICA": "total_nomina_electronica",
        "AJUSTE_NOMINA": "total_ajuste_nomina",
        "NOTA_AJUSTE": "total_nota_ajuste",
    }

    if tipo not in mapa:
        raise HTTPException(400, f"Tipo desconocido: {tipo}")

    setattr(m, mapa[tipo], getattr(m, mapa[tipo]) + 1)
    setattr(a, mapa[tipo], getattr(a, mapa[tipo]) + 1)

    db.commit()
    recalcular_saldo_resumenes(db, cliente_id, anio, mes)


# ======================================================
# 🔒 VALIDAR MES ABIERTO
# ======================================================
def validar_mes_abierto(db: Session, cliente_id: int, fecha: date):

    resumen = db.query(ResumenMensual).filter_by(
        cliente_id=cliente_id,
        anio=fecha.year,
        mes=fecha.month
    ).first()

    if not resumen:
        raise HTTPException(400, "No existe resumen mensual")

    if resumen.estado == "cerrado":
        raise HTTPException(409, "El mes está cerrado")

    return resumen


# ======================================================
# 📅 CIERRE AUTOMÁTICO MENSUAL
# ======================================================
def cierre_mensual_automatico(db: Session, cliente_id: int, fecha: date):

    anio, mes = fecha.year, fecha.month
    anio_ant, mes_ant = (anio - 1, 12) if mes == 1 else (anio, mes - 1)

    anterior = db.query(ResumenMensual).filter_by(
        cliente_id=cliente_id, anio=anio_ant, mes=mes_ant
    ).first()

    if anterior and anterior.estado == "abierto":
        anterior.estado = "cerrado"

    actual = db.query(ResumenMensual).filter_by(
        cliente_id=cliente_id, anio=anio, mes=mes
    ).first()

    if not actual:
        raise HTTPException(500, "No existe resumen mensual")

    actual.estado = "abierto"

    if actual.saldo_inicial == 0:
        cliente = db.query(Cliente).get(cliente_id)
        actual.saldo_inicial = cliente.saldo_actual
        actual.saldo_final = cliente.saldo_actual

    db.commit()


# ======================================================
# 🧾 CIERRE ANUAL GLOBAL (MANUAL)
# ======================================================
def cierre_anual_manual(db: Session, anio: int):

    clientes = db.query(Cliente).all()
    nuevo_anio = anio + 1

    for cliente in clientes:

        # 🔒 Cerrar todos los meses del año
        meses = db.query(ResumenMensual).filter_by(
            cliente_id=cliente.id, anio=anio
        ).all()

        for m in meses:
            m.estado = "cerrado"

        # 📌 Congelar resumen anual
        resumen_anual = db.query(ResumenAnual).filter_by(
            cliente_id=cliente.id, anio=anio
        ).first()

        if resumen_anual:
            resumen_anual.saldo_final = cliente.saldo_actual

        # 🆕 Crear nuevo resumen anual
        nuevo_anual = ResumenAnual(
            cliente_id=cliente.id,
            anio=nuevo_anio,
            saldo_inicial=cliente.saldo_actual,
            saldo_final=cliente.saldo_actual
        )
        db.add(nuevo_anual)

        # 🆕 Crear meses del nuevo año
        for mes in range(1, 13):
            db.add(ResumenMensual(
                cliente_id=cliente.id,
                anio=nuevo_anio,
                mes=mes,
                estado="abierto" if mes == 1 else "cerrado",
                saldo_inicial=cliente.saldo_actual if mes == 1 else 0,
                saldo_final=cliente.saldo_actual if mes == 1 else 0
            ))

    db.commit()

    return {"msg": f"Año {anio} cerrado y {nuevo_anio} creado correctamente"}
# ======================================================
# 📌 OBTENER RESUMEN MENSUAL POR NIT
# ======================================================
def resumen_mensual_por_nit(
    db: Session,
    nit: str,
    anio: int,
    mes: int
):
    cliente = db.query(Cliente).filter_by(nit=nit).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    resumen = db.query(ResumenMensual).filter_by(
        cliente_id=cliente.id,
        anio=anio,
        mes=mes
    ).first()

    return resumen


# ======================================================
# 📌 OBTENER RESUMEN ANUAL POR NIT
# ======================================================
def resumen_anual_por_nit(
    db: Session,
    nit: str,
    anio: int
):
    cliente = db.query(Cliente).filter_by(nit=nit).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    resumen = db.query(ResumenAnual).filter_by(
        cliente_id=cliente.id,
        anio=anio
    ).first()

    return resumen
# ======================================================
# 📊 RESÚMENES MENSUALES DEL AÑO POR NIT
# ======================================================
def resumenes_mensuales_anio_por_nit(
    db: Session,
    nit: str,
    anio: int
):
    cliente = db.query(Cliente).filter_by(nit=nit).first()
    if not cliente:
        raise HTTPException(404, "Cliente no encontrado")

    resumenes = (
        db.query(ResumenMensual)
        .filter(
            ResumenMensual.cliente_id == cliente.id,
            ResumenMensual.anio == anio
        )
        .order_by(ResumenMensual.mes.asc())
        .all()
    )

    if not resumenes:
        raise HTTPException(
            status_code=404,
            detail=f"No existen resúmenes para el año {anio}"
        )

    return resumenes
