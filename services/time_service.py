from datetime import date, datetime
from zoneinfo import ZoneInfo
import os

# Zona horaria fija de Colombia (sin horario de verano)
BOGOTA_TZ = ZoneInfo("America/Bogota")


def obtener_fecha_actual() -> date:
    """
    Devuelve la fecha actual en Bogotá (America/Bogota).
    
    - Si existe FECHA_PRUEBA → usa esa fecha (formato YYYY-MM-DD)
    - Si no → usa la fecha real en zona horaria de Bogotá
    """
    fecha_prueba = os.getenv("FECHA_PRUEBA")
    
    # Debug (puedes quitarlo en producción o dejarlo con logging)
    if fecha_prueba:
        print(f"FECHA_PRUEBA detectada: {fecha_prueba}")
    
    if fecha_prueba:
        try:
            return date.fromisoformat(fecha_prueba)
        except ValueError as e:
            print(f"Error en formato de FECHA_PRUEBA: {e}. Usando fecha real.")
            # O podrías raise ValueError si prefieres fallar fuerte en pruebas

    # Fecha real → SIEMPRE en zona Bogotá
    return datetime.now(BOGOTA_TZ).date()