import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Cargar variables del .env
load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

DESTINATARIO = EMAIL_USER  # te lo envías a ti mismo para la prueba

def enviar_correo_prueba():
    mensaje = MIMEMultipart()
    mensaje["From"] = EMAIL_USER
    mensaje["To"] = DESTINATARIO
    mensaje["Subject"] = "✅ Prueba de correo - Folios Control"

    cuerpo = """
Hola 👋

Este es un correo de prueba enviado desde el proyecto Folios Control.

Si recibes esto, la configuración SMTP funciona correctamente 🚀
"""
    mensaje.attach(MIMEText(cuerpo, "plain"))

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(mensaje)
        server.quit()

        print("✅ Correo enviado correctamente")

    except Exception as e:
        print("❌ Error enviando correo:")
        print(e)


if __name__ == "__main__":
    enviar_correo_prueba()
