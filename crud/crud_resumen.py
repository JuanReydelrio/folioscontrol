from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import date, timedelta

from models.resumen_mensual_model import ResumenMensual
from models.resumen_anual_model import ResumenAnual
from models.cliente_model import Cliente

from services.time_service import obtener_fecha_actual
#======================================================
# validar si un resumen tiene movimientos
#======================================================

def resumen_tiene_movimientos(resumen: ResumenMensual) -> bool:
    return any([
        resumen.total_entradas or 0,
        resumen.total_ajustes or 0,
        resumen.total_facturas or 0,
        resumen.total_notas_credito or 0,
        resumen.total_notas_debito or 0,
        resumen.total_documentos_soporte or 0,
        resumen.total_ajuste_documentos_soporte or 0,
        resumen.total_nomina_electronica or 0,
        resumen.total_ajuste_nomina or 0,
        resumen.total_nota_ajuste or 0,
    ])
#=====================================================
# obtener periodo anterior
#=====================================================
def obtener_periodo_anterior(anio: int, mes: int):
    """
    Retorna (anio, mes) del período inmediatamente anterior.
    Maneja correctamente el cambio de año.
    """
    if mes == 1:
        return anio - 1, 12

    return anio, mes - 1

#======================================================
# determinar si un resumen representa actividad real
# o un saldo financiero existente
#======================================================

def resumen_es_significativo(resumen: ResumenMensual) -> bool:
    """
    Determina si el resumen representa un período real
    dentro de la historia financiera del cliente.

    Se considera significativo si tiene:
    - Movimientos.
    - Saldo inicial diferente de cero.
    - Saldo final diferente de cero.
    """

    tiene_movimientos = resumen_tiene_movimientos(resumen)

    tiene_saldo = (
        (resumen.saldo_inicial or 0) != 0
        or (resumen.saldo_final or 0) != 0
    )

    return tiene_movimientos or tiene_saldo
#=====================================================
# sincronizar resúmenes de un cliente
#=====================================================

def sincronizar_resumenes_cliente(
    db: Session,
    cliente_id: int,
    fecha: date | None = None
):
    """
    Sincroniza los resúmenes mensuales de un cliente
    hasta el mes indicado.

    Reglas:

    1. No modifica meses futuros.
    2. Busca automáticamente el primer período financiero
       significativo del cliente.
    3. Los meses anteriores al período ancla no se modifican.
    4. El período ancla conserva sus valores.
    5. Los meses posteriores sin movimientos heredan el saldo
       final del período anterior.
    6. Los meses con movimientos conservan sus movimientos.
    7. Los meses anteriores al actual quedan cerrados.
    8. El mes actual queda abierto.
    """

    cliente = db.query(Cliente).filter_by(
        id=cliente_id
    ).first()

    if not cliente:
        raise HTTPException(
            404,
            "Cliente no encontrado"
        )

    fecha = fecha or obtener_fecha_actual()

    anio_actual = fecha.year
    mes_actual = fecha.month

    # ==================================================
    # OBTENER RESÚMENES HASTA EL MES ACTUAL
    # ==================================================

    resumenes = (
        db.query(ResumenMensual)
        .filter(
            ResumenMensual.cliente_id == cliente_id,
            (
                (ResumenMensual.anio < anio_actual)
                |
                (
                    (ResumenMensual.anio == anio_actual)
                    &
                    (ResumenMensual.mes <= mes_actual)
                )
            )
        )
        .order_by(
            ResumenMensual.anio.asc(),
            ResumenMensual.mes.asc()
        )
        .all()
    )

    if not resumenes:
        return

    # ==================================================
    # BUSCAR EL MES ANCLA
    # ==================================================
    #
    # El mes ancla es el primer período que demuestra
    # existencia financiera real del cliente.
    #
    # Puede tener:
    # - saldo inicial
    # - saldo final
    # - movimientos
    # ==================================================

    indice_ancla = None

    for indice, resumen in enumerate(resumenes):

        if resumen_es_significativo(resumen):

            indice_ancla = indice
            break

    # ==================================================
    # SI NO HAY NINGÚN SALDO NI MOVIMIENTO
    # NO HAY NADA QUE SINCRONIZAR
    # ==================================================

    if indice_ancla is None:

        # Solo actualizamos estados
        for resumen in resumenes:

            if (
                resumen.anio == anio_actual
                and resumen.mes == mes_actual
            ):
                resumen.estado = "abierto"
            else:
                resumen.estado = "cerrado"

        db.flush()
        return

    # ==================================================
    # EL MES ANCLA CONSERVA SU SALDO
    # ==================================================

    resumen_ancla = resumenes[indice_ancla]

    saldo_anterior = resumen_ancla.saldo_final

    if saldo_anterior is None:
        saldo_anterior = resumen_ancla.saldo_inicial or 0

    # ==================================================
    # RECORRER TODOS LOS RESÚMENES
    # ==================================================

    for indice, resumen in enumerate(resumenes):

        # ----------------------------------------------
        # MESES ANTERIORES AL ANCLA
        # ----------------------------------------------
        #
        # Son registros creados automáticamente antes de
        # que existiera actividad financiera del cliente.
        #
        # NO SE TOCAN LOS SALDOS.
        # ----------------------------------------------

        if indice < indice_ancla:

            if (
                resumen.anio == anio_actual
                and resumen.mes == mes_actual
            ):
                resumen.estado = "abierto"
            else:
                resumen.estado = "cerrado"

            continue

        # ----------------------------------------------
        # MES ANCLA
        # ----------------------------------------------
        #
        # Se respeta completamente.
        # ----------------------------------------------

        if indice == indice_ancla:

            if (
                resumen.anio == anio_actual
                and resumen.mes == mes_actual
            ):
                resumen.estado = "abierto"
            else:
                resumen.estado = "cerrado"

            saldo_anterior = resumen.saldo_final

            if saldo_anterior is None:
                saldo_anterior = resumen.saldo_inicial or 0

            continue

        # ----------------------------------------------
        # MESES POSTERIORES AL ANCLA
        # ----------------------------------------------

        if not resumen_tiene_movimientos(resumen):

            # Mes vacío:
            # hereda el saldo anterior

            resumen.saldo_inicial = saldo_anterior
            resumen.saldo_final = saldo_anterior

        else:

            # Mes con movimientos:
            # El saldo inicial debe venir del mes anterior.
            #
            # IMPORTANTE:
            # No recalculamos aquí los movimientos porque
            # cada CRUD ya actualiza sus propios totales.

            resumen.saldo_inicial = saldo_anterior

        # ----------------------------------------------
        # ACTUALIZAR ESTADO
        # ----------------------------------------------

        if (
            resumen.anio == anio_actual
            and resumen.mes == mes_actual
        ):
            resumen.estado = "abierto"
        else:
            resumen.estado = "cerrado"

        # ----------------------------------------------
        # PREPARAR SALDO PARA EL SIGUIENTE MES
        # ----------------------------------------------

        saldo_anterior = resumen.saldo_final or 0

    db.flush()

#=====================================================
# recalcular saldo de resúmenes
#=====================================================

def recalcular_saldo_resumenes(db: Session, cliente_id: int, anio: int, mes: int):

    cliente = db.query(Cliente).filter_by(id=cliente_id).first()
    if not cliente:
        return  # helper silencioso

    resumen_m = db.query(ResumenMensual).filter_by(
        cliente_id=cliente_id, anio=anio, mes=mes
    ).first()

    resumen_a = db.query(ResumenAnual).filter_by(
        cliente_id=cliente_id, anio=anio
    ).first()

    # Si no existen aún, no es error
    if not resumen_m or not resumen_a:
        return

    # 🔒 No tocar meses cerrados
    if resumen_m.estado == "cerrado":
        return

    resumen_m.saldo_final = cliente.saldo_actual
    resumen_a.saldo_final = cliente.saldo_actual

    db.flush()

def verificar_cambio_anio(
    db: Session,
    fecha: date
):
    """
    Verifica si el año de la operación ya está preparado.

    Si detecta que algún cliente todavía no tiene el resumen anual
    del año actual, cierra el año anterior y prepara el nuevo año.

    El proceso es global para todos los clientes:
    - Sincroniza el año anterior.
    - Cierra todos sus resúmenes mensuales.
    - Cierra y congela el resumen anual.
    - Crea el resumen anual del nuevo año.
    - Crea los 12 meses del nuevo año:
        enero abierto
        febrero-diciembre cerrados.
    """

    anio_actual = fecha.year
    anio_anterior = anio_actual - 1

    clientes = db.query(Cliente).all()

    if not clientes:
        return

    # ==================================================
    # VERIFICAR SI EL AÑO YA ESTÁ PREPARADO
    # ==================================================

    clientes_pendientes = []

    for cliente in clientes:

        resumen_actual = db.query(ResumenAnual).filter_by(
            cliente_id=cliente.id,
            anio=anio_actual
        ).first()

        if not resumen_actual:
            clientes_pendientes.append(cliente)

    # Si todos los clientes ya tienen el nuevo año,
    # no hacemos absolutamente nada.
    if not clientes_pendientes:
        return

    # ==================================================
    # PROCESAR CLIENTES PENDIENTES
    # ==================================================

    for cliente in clientes_pendientes:

        # ----------------------------------------------
        # 1. SINCRONIZAR AÑO ANTERIOR
        # ----------------------------------------------

        sincronizar_resumenes_cliente(
            db=db,
            cliente_id=cliente.id,
            fecha=date(anio_anterior, 12, 31)
        )

        # ----------------------------------------------
        # 2. CERRAR TODOS LOS MESES DEL AÑO ANTERIOR
        # ----------------------------------------------

        db.query(ResumenMensual).filter(
            ResumenMensual.cliente_id == cliente.id,
            ResumenMensual.anio == anio_anterior
        ).update(
            {
                "estado": "cerrado"
            },
            synchronize_session=False
        )

        # ----------------------------------------------
        # 3. CERRAR Y CONGELAR RESUMEN ANUAL ANTERIOR
        # ----------------------------------------------

        resumen_anterior = db.query(ResumenAnual).filter_by(
            cliente_id=cliente.id,
            anio=anio_anterior
        ).first()

        if resumen_anterior:

            resumen_anterior.estado = "cerrado"

            # Tomamos el saldo final del último resumen mensual
            diciembre = db.query(ResumenMensual).filter_by(
                cliente_id=cliente.id,
                anio=anio_anterior,
                mes=12
            ).first()

            if diciembre:
                saldo_cierre = diciembre.saldo_final
            else:
                saldo_cierre = cliente.saldo_actual

            resumen_anterior.saldo_final = saldo_cierre

        # ----------------------------------------------
        # 4. CREAR RESUMEN ANUAL DEL NUEVO AÑO
        # ----------------------------------------------

        saldo_inicial_nuevo_anio = (
            resumen_anterior.saldo_final
            if resumen_anterior
            else cliente.saldo_actual
        )

        nuevo_anual = ResumenAnual(
            cliente_id=cliente.id,
            anio=anio_actual,
            estado="abierto",
            saldo_inicial=saldo_inicial_nuevo_anio,
            saldo_final=saldo_inicial_nuevo_anio
        )

        db.add(nuevo_anual)

        # ----------------------------------------------
        # 5. CREAR LOS 12 MESES DEL NUEVO AÑO
        # ----------------------------------------------

        for mes in range(1, 13):

            es_enero = mes == 1

            nuevo_mensual = ResumenMensual(
                cliente_id=cliente.id,
                anio=anio_actual,
                mes=mes,
                estado="abierto" if es_enero else "cerrado",
                saldo_inicial=(
                    saldo_inicial_nuevo_anio
                    if es_enero
                    else 0
                ),
                saldo_final=(
                    saldo_inicial_nuevo_anio
                    if es_enero
                    else 0
                )
            )

            db.add(nuevo_mensual)

    # Hacemos visibles los cambios para el resto
    # del flujo, pero NO confirmamos la transacción aquí.
    db.flush()


# ======================================================
# ➕ ENTRADAS
# ======================================================
def sumar_entrada(db: Session, cliente_id: int, cantidad: int, fecha: date):

    verificar_cambio_anio(db, fecha)    

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

   
    recalcular_saldo_resumenes(db, cliente_id, anio, mes)
    db.flush()

# ======================================================
# restar entradas (para eliminar entradas erroneas)
# ======================================================    

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

    
    recalcular_saldo_resumenes(db, cliente_id, anio, mes)
    db.flush()

# ======================================================
# ➖ SALIDAS (DOCUMENTOS)
# ======================================================
def sumar_salida(db: Session, cliente_id: int, tipo: str, fecha: date | None):

    fecha = fecha or obtener_fecha_actual()
    #==============================================
    # verifcar cambio de año
    #==============================================
    verificar_cambio_anio(db, fecha)

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
        "AJUSTE_DOCUMENTO_SOPORTE": "total_ajuste_documentos_soporte",
        "NOMINA_ELECTRONICA": "total_nomina_electronica",
        "AJUSTE_NOMINA": "total_ajuste_nomina",
        "NOTA_AJUSTE": "total_nota_ajuste",
    }

    if tipo not in mapa:
        raise HTTPException(400, f"Tipo desconocido: {tipo}")

    setattr(m, mapa[tipo], getattr(m, mapa[tipo]) + 1)
    setattr(a, mapa[tipo], getattr(a, mapa[tipo]) + 1)

  
    recalcular_saldo_resumenes(db, cliente_id, anio, mes)

    db.flush()


#======================================================
# + sumar ajuste
#=====================================================
def sumar_ajuste(db: Session, cliente_id: int, cantidad: int, fecha: date):

    verificar_cambio_anio(db, fecha)

    m = db.query(ResumenMensual).filter_by(
        cliente_id=cliente_id,
        anio=fecha.year,
        mes=fecha.month
    ).first()

    a = db.query(ResumenAnual).filter_by(
        cliente_id=cliente_id,
        anio=fecha.year
    ).first()

    if not m or not a:
        raise HTTPException(409, "Resumen no encontrado")

    m.total_ajustes += cantidad
    a.total_ajustes += cantidad

    recalcular_saldo_resumenes(db, cliente_id, fecha.year, fecha.month)

    db.flush()


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
def cierre_mensual_automatico(
    db: Session,
    cliente_id: int,
    fecha: date
):
    """
    Prepara los resúmenes del cliente antes de registrar
    un movimiento en el mes indicado.

    Sincroniza los meses anteriores que estén vacíos
    y garantiza que el mes actual esté abierto.
    """

    # Sincronizar todos los meses hasta el mes actual.
    sincronizar_resumenes_cliente(
        db=db,
        cliente_id=cliente_id,
        fecha=fecha
    )

    # Verificar que exista el resumen del mes actual.
    actual = db.query(ResumenMensual).filter_by(
        cliente_id=cliente_id,
        anio=fecha.year,
        mes=fecha.month
    ).first()

    if not actual:
        raise HTTPException(
            500,
            "No existe resumen mensual"
        )

    # El mes donde se realizará el movimiento
    # debe permanecer abierto.
    actual.estado = "abierto"

    db.flush()
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

    # --------------------------------------------------
    # Sincronizar antes de consultar
    # --------------------------------------------------
    sincronizar_resumenes_cliente(
        db=db,
        cliente_id=cliente.id,
        fecha=obtener_fecha_actual()
    )

    # --------------------------------------------------
    # Consultar resúmenes del año solicitado
    # --------------------------------------------------
    resumenes = (
        db.query(ResumenMensual)
        .filter(
            ResumenMensual.cliente_id == cliente.id,
            ResumenMensual.anio == anio
        )
        .order_by(
            ResumenMensual.mes.asc()
        )
        .all()
    )

    if not resumenes:
        raise HTTPException(
            status_code=404,
            detail=f"No existen resúmenes para el año {anio}"
        )

    return resumenes


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
    # --------------------------------------------------
    # Sincronizar antes de consultar
    # --------------------------------------------------
    sincronizar_resumenes_cliente(
        db=db,
        cliente_id=cliente.id,
        fecha=obtener_fecha_actual()
    )
    db.commit()
    
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