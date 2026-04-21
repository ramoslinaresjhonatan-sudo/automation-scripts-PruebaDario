import json
import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Integration.WhatsApp import WhatsApp

def cargar_config():
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Config.json'))
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

async def procesar_copypage():
    config = cargar_config()
    data = config.get("CopyPage", {})
    
    chats = data.get("envio_Whatsapp", [])
    rutas_archivos = data.get("rutas", [])
    resumen_ruta = data.get("resumen_ruta")
    
    envio_de_rutas = data.get("envio_de_rutas", False)
    envio_resumen = data.get("envio_Resumen", False)
    
    if not chats:
        print("[INFO] No hay chats configurados en CopyPage.")
        return

    wa = WhatsApp()
    
    try:
        if not await wa.conectar():
            print("[ERROR] No se pudo conectar a WhatsApp.")
            return

        for chat in chats:
            if envio_de_rutas and rutas_archivos:
                archivos_validos = [r for r in rutas_archivos if os.path.exists(r)]
                if archivos_validos:
                    print(f"[INFO] Enviando archivos de CopyPage a {chat}...")
                    await wa.enviar(chat, archivos=archivos_validos)
                else:
                    print(f"[WARNING] No se encontraron los archivos especificados en 'rutas' para {chat}.")
            
            if envio_resumen and resumen_ruta:
                if os.path.exists(resumen_ruta):
                    print(f"[INFO] Enviando resumen de CopyPage a {chat}...")
                    try:
                        with open(resumen_ruta, 'r', encoding='utf-8') as fr:
                            contenido = fr.read()
                        if contenido.strip():
                            await wa.mensaje(chat, f"*Resumen de CopyPage*\n\n{contenido}")
                        else:
                            print(f"[WARNING] El archivo de resumen está vacío: {resumen_ruta}")
                    except Exception as e:
                        print(f"[ERROR] No se pudo leer el archivo de resumen: {e}")
                else:
                    print(f"[WARNING] No se encontro el archivo de resumen: {resumen_ruta}")
    finally:
        await wa.cerrar()

if __name__ == "__main__":
    asyncio.run(procesar_copypage())
