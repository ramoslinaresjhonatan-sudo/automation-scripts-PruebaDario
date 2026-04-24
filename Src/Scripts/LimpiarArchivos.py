import os
import sys
import json
import asyncio
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from Src.Utilities.LimpiarArchivosProceso import LimpiadorLogs
from Src.Integrations.WhatsApp import WhatsApp as WhatsAppSender


def cargar_json(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def crear_logger(escenario=None):
    log_dir = os.path.join(BASE_DIR, "Logs")
    os.makedirs(log_dir, exist_ok=True)

    fecha = datetime.now().strftime("%Y-%m-%d")
    nombre_base = "LimpiadorLog"
    
    if escenario:
        nombre_log = f"{nombre_base}-{fecha}-{escenario}.log"
    else:
        nombre_log = f"{nombre_base}-{fecha}.log"

    ruta = os.path.join(log_dir, nombre_log)

    def log(msg):
        linea = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        print(linea)
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(linea + "\n")

    return log


async def main():
    try:
        config_path = os.path.join(BASE_DIR, "Config", "LimpiadorLog.json")
        config = cargar_json(config_path)

        whatsapp = WhatsAppSender()
        if not await whatsapp.conectar():
            print("[ERROR] No se pudo conectar a WhatsApp.")
        
        ahora = datetime.now()
        reporte_txt = f"fecha: {ahora.strftime('%d-%m-%Y')}\n"
        reporte_txt += f"hora: {ahora.strftime('%H:%M')}\n"
        reporte_txt += "----------------------------\n"

        for conf in config["datos"]:
            escenario = conf['nombre'].replace(" ", "_")
            logger = crear_logger(escenario)
            logger(f"[INFO] Iniciando limpieza de escenario: {conf['nombre']}")

            limpiador = LimpiadorLogs()
            total, espacio, eliminados = limpiador.limpiar(conf, logger)

            mb = espacio / (1024 * 1024)
            
            resumen_msg = (
                f"*{conf['nombre']}*\n"
                f"*Resumen:*\n"
                f". Archivos borrados: {total}\n"
                f". Espacio liberado: {mb:.2f} MB"
            )
            
            reporte_txt += resumen_msg + "\n----------------------------\n"

            for chat in config.get("chats", []):
                logger(f"[INFO] Enviando reporte a WhatsApp: {chat}")
                await whatsapp.mensaje(chat, resumen_msg)

        mensajes_dir = os.path.join(BASE_DIR, "Mensajes")
        os.makedirs(mensajes_dir, exist_ok=True)
        ruta_mensaje = os.path.join(mensajes_dir, "Resumen-Limpieza.txt")
        
        with open(ruta_mensaje, "w", encoding="utf-8") as f:
            f.write(reporte_txt)
        
        print(f"[INFO] Mensaje de resumen guardado en: {ruta_mensaje}")
        
        await whatsapp.cerrar()
        print("[INFO] Proceso de limpieza completado de forma exitosa.")
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Excepcion no controlada en LimpiarArchivos: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())