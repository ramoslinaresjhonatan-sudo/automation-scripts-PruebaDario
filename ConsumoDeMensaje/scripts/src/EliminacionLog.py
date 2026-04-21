import json
import os
import sys
import asyncio

# Agregar el directorio base al path para importar la integración de WhatsApp
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Integration.WhatsApp import WhatsApp

def cargar_config():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Config.json'))
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

async def procesar_eliminacion_log():
    config = cargar_config()
    data = config.get("deleteLog", {})
    
    chats = data.get("envio_Whatsapp", [])
    resumen_ruta = data.get("resumen_rutas")
    envio_resumen = data.get("envio_Resumen", False)
    
    if not chats:
        print("[INFO] No hay chats configurados en deleteLog.")
        return

    wa = WhatsApp()
    
    try:
        if not await wa.conectar():
            print("[ERROR] No se pudo conectar a WhatsApp.")
            return

        for chat in chats:
            # Enviar resumen si está habilitado
            if envio_resumen and resumen_ruta:
                if os.path.exists(resumen_ruta):
                    print(f"[INFO] Enviando resumen de EliminacionLog a {chat}...")
                    try:
                        with open(resumen_ruta, 'r', encoding='utf-8') as fr:
                            contenido = fr.read()
                        if contenido.strip():
                            await wa.mensaje(chat, f"*Resumen de Eliminación de Logs*\n\n{contenido}")
                        else:
                            print(f"[WARNING] El archivo de resumen está vacío: {resumen_ruta}")
                    except Exception as e:
                        print(f"[ERROR] No se pudo leer el archivo de resumen: {e}")
                else:
                    print(f"[WARNING] No se encontro el archivo de resumen: {resumen_ruta}")
    finally:
        await wa.cerrar()

if __name__ == "__main__":
    asyncio.run(procesar_eliminacion_log())
