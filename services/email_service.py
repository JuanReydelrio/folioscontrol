import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

DESTINATARIOS_ALERTA = os.getenv("EMAIL_ALERTAS", "").split(",")

def enviar_alerta_folios(cliente_nombre: str, nit: str, mensaje: str, saldo: int):
    if not DESTINATARIOS_ALERTA or DESTINATARIOS_ALERTA == [""]:
        print("⚠️ No hay destinatarios configurados para alertas")
        return

    asunto = f"⚠️ ALERTA FOLIOS CLIENTE {cliente_nombre}"

    cuerpo = f"""
    🚨 ALERTA AUTOMÁTICA DE FOLIOS 🚨

    Cliente: {cliente_nombre}
    NIT: {nit}

    Estado:
    {mensaje}

    Saldo actual: {saldo}

    Fecha evento: sistema automático
    """

    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = ", ".join(DESTINATARIOS_ALERTA)
    msg["Subject"] = asunto
    msg.attach(MIMEText(cuerpo, "plain"))

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, DESTINATARIOS_ALERTA, msg.as_string())
        server.quit()
        print("📧 Correo de alerta enviado")
    except Exception as e:
        print(f"❌ Error enviando correo: {e}")
