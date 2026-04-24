import os
import sys
import time
import json
import shutil
import threading
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from Src.Integrations.WhatsApp import WhatsApp

def resource_path(filename):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.abspath(filename)


def formato_bytes(bytes_):
    if bytes_ >= 1024**3:
        return f"{bytes_ / (1024**3):.2f} GB"
    elif bytes_ >= 1024**2:
        return f"{bytes_ / (1024**2):.2f} MB"
    elif bytes_ >= 1024:
        return f"{bytes_ / 1024:.2f} KB"
    return f"{bytes_} B"


def enviar_correo_error(archivo_error, smtp_service, asunto):
    try:
        mensaje = (
            "Estimados,\n\n"
            "Se adjunta el resultado del proceso de copia.\n\n"
            "Saludos."
        )

        smtp_service.send_mail(
            subject=asunto,
            to=smtp_service.error_recipients,
            message=mensaje,
            attachments=archivo_error
        )

        print(f"[INFO] Correo enviado a {smtp_service.error_recipients}")

    except Exception as e:
        print(f"[ERROR] Fallo al enviar correo: {e}")


def construir_mensaje_resumen(tareas_ok, tareas_error):
    ahora = datetime.now()
    fecha = ahora.strftime('%d-%m-%Y')
    hora = ahora.strftime('%H:%M')
    
    mensaje = (
        f"*Resumen de Copiado Pegado de PROD a DESA*\n\n"
        f"fecha: {fecha}\n"
        f"hora: {hora}\n\n"
        f"*Copiado de archivos*\n"
        f"----------------------------------------\n"
        f"*Estado De Copiado*\n"
    )

    all_tareas = tareas_ok + tareas_error
    for i, t in enumerate(all_tareas, 1):
        status = "[EXITO ]" if t in tareas_ok else "[ERROR]"
        mensaje += f"{i}. {status}: {t['nombre']}\n"
    
    mensaje += "---------------------------------------\n"
    mensaje += "*Detalle De Incremento*\n"
    
    for i, t in enumerate(all_tareas, 1):
        bytes_val = t.get("bytes_copiados", 0)
        gb_val = bytes_val / (1024**3)
        # Formato con comas para miles y 3 decimales si es necesario, o según el ejemplo del usuario: 15,325
        # El ejemplo del usuario 15,325 parece usar coma como separador de miles o como decimal? 
        # En muchos países hispanos la coma es decimal. Pero "15,325 (Gbytes)" sugiere GigaBytes.
        # Usaremos formato con comas para miles y 3 decimales.
        mensaje += f"{i}. incremento: {gb_val:,.3f} (Gbytes)\n"
        
    mensaje += "--------------------------------------\n"
    mensaje += "*Espacio de Memoria*\n"
    
    drives_processed = set()
    drive_idx = 1
    for t in all_tareas:
        destino = t.get("destino")
        if not destino:
            continue
            
        drive_letter = os.path.splitdrive(destino)[0]
        if not drive_letter and destino.startswith("\\\\"):
            # Caso de ruta UNC: Tomar la primera parte como el "disco"
            parts = destino.split('\\')
            if len(parts) > 3:
                drive_letter = f"\\\\{parts[2]}\\{parts[3]}"
            else:
                drive_letter = destino
        
        if drive_letter and drive_letter not in drives_processed:
            try:
                usage = shutil.disk_usage(destino)
                free_gb = usage.free / (1024**3)
                # Extraer solo la letra si es un disco local (ej: D: -> D)
                display_drive = drive_letter.replace(":", "") if ":" in drive_letter else drive_letter
                mensaje += f"{drive_idx}. [{display_drive}]: {free_gb:,.2f} (Gbytes)\n"
                drives_processed.add(drive_letter)
                drive_idx += 1
            except:
                pass
                
    return mensaje


async def enviar_whatsapp_resumen_tareas(tareas_exitosas, tareas_con_errores, wa_config):
    try:
        if not wa_config.get("Activo"):
            return
        chats = wa_config.get("numero", [])
        if not chats:
            return

        enviar_con_imagen = wa_config.get("image", True)
        enviar_con_texto = wa_config.get("texto", True)

        archivos_envio = []

        # Si hay errores y queremos adjuntar el archivo de log
        for t_err in tareas_con_errores:
            if t_err.get('log_path') and os.path.exists(t_err['log_path']):
                archivos_envio.append(t_err['log_path'])

        sender = WhatsApp()
        if not await sender.conectar():
            print("[ERROR] No se pudo conectar a WhatsApp para enviar el resumen.")
            return

        mensaje = construir_mensaje_resumen(tareas_exitosas, tareas_con_errores) if enviar_con_texto else None

        if mensaje:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            mensajes_dir = os.path.join(project_root, "Mensajes")
            os.makedirs(mensajes_dir, exist_ok=True)
            ruta_mensaje = os.path.join(mensajes_dir, f"Resumen-copypage.txt")
            with open(ruta_mensaje, "w", encoding="utf-8") as f:
                f.write(mensaje)
            print(f"[INFO] Mensaje guardado en: {ruta_mensaje}")

        for chat in chats:
            print(f"[INFO] Enviando reporte a {chat}")
            await sender.enviar(chat, mensaje=mensaje, archivos=archivos_envio)
        
        await sender.cerrar()

    except Exception as e:
        print(f"[ERROR] Fallo al enviar mensaje de WhatsApp: {e}")

def crear_rutas_logs(nombre):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    logs = os.path.join(project_root, "Logs")
    storage = os.path.join(project_root, "Storage")
    mensajes = os.path.join(project_root, "Mensajes")
    os.makedirs(logs, exist_ok=True)
    os.makedirs(storage, exist_ok=True)
    os.makedirs(mensajes, exist_ok=True)
    fecha = datetime.now().strftime('%d-%m-%Y')
    log = os.path.join(logs, f"CopyPage-{fecha}-{nombre}.log")
    err = os.path.join(storage, f"ListaArchivoErrores-{nombre}.txt")
    return log, err

def registrar(f_log, mensaje):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f_log.write(f"[{ts}] {mensaje}\n")

def validar_archivo(archivo, solo_qvd, dias, fecha_actual):
    if not archivo.is_file():
        return False

    if solo_qvd and not archivo.name.lower().endswith(".qvd"):
        return False

    if dias is not None:
        mtime = datetime.fromtimestamp(archivo.stat().st_mtime)
        if mtime < fecha_actual - timedelta(days=dias):
            return False
    return True


def copiar_archivo(origen, destino, libre_actual):
    tam_origen = origen.stat().st_size
    tam_dest = os.path.getsize(destino) if os.path.exists(destino) else 0

    if os.path.exists(destino) and tam_origen == tam_dest:
        return "omitido", 0

    diff = max(tam_origen - tam_dest, 0)

    if libre_actual < diff:
        return "sin_espacio", diff

    shutil.copy2(str(origen), str(destino))
    return "copiado", diff


def copiar_archivos_modificados(nombre, origen, destino, dias_para_considerar=None, solo_qvd=False):
    try:
        inicio = time.time()
        fecha_actual = datetime.now()
        origen_path = Path(origen).resolve()
        destino_path = Path(destino).resolve()

        os.makedirs(destino, exist_ok=True)

        log_path, err_path = crear_rutas_logs(nombre)
        
        total_bytes_copiados = 0
        copiados, omitidos = 0, 0
        errores = {}
        todos_los_errores = []
        
        _, _, libre = shutil.disk_usage(destino)
        
        lock = threading.Lock()
        dir_cache = {str(destino_path)}

        def proceso_archivo(archivo):
            nonlocal libre, copiados, omitidos, total_bytes_copiados
            try:
                # Validar si el archivo es el propio destino para evitar recursión infinita
                try:
                    if destino_path in archivo.resolve().parents or archivo.resolve() == destino_path:
                        return None
                except Exception:
                    pass

                stat = archivo.stat()
                if not stat.st_size and not archivo.is_file():
                    return None

                if solo_qvd and not archivo.name.lower().endswith(".qvd"):
                    return None

                if dias_para_considerar is not None:
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    if mtime < fecha_actual - timedelta(days=dias_para_considerar):
                        return None

                rel_path = os.path.relpath(archivo, origen)
                destino_ruta = os.path.join(destino, rel_path)
                
                # Optimizar creación de directorios
                parent_dir = os.path.dirname(destino_ruta)
                if parent_dir not in dir_cache:
                    with lock:
                        if parent_dir not in dir_cache:
                            os.makedirs(parent_dir, exist_ok=True)
                            dir_cache.add(parent_dir)

                tam_origen = stat.st_size
                tam_dest = os.path.getsize(destino_ruta) if os.path.exists(destino_ruta) else -1

                if tam_origen == tam_dest:
                    with lock:
                        omitidos += 1
                    return f"OMITIDO {archivo}"

                diff = max(tam_origen - (tam_dest if tam_dest > 0 else 0), 0)

                with lock:
                    if libre < diff:
                        errores.setdefault("DISCO LLENO", []).append(str(archivo))
                        todos_los_errores.append(str(archivo))
                        return f"ERROR espacio {archivo}"

                shutil.copy2(str(archivo), str(destino_ruta))
                
                with lock:
                    copiados += 1
                    libre -= diff
                    total_bytes_copiados += tam_origen
                return f"COPIADO {archivo} ({formato_bytes(tam_origen)})"

            except Exception as e:
                with lock:
                    errores.setdefault("GENERAL", []).append(str(archivo))
                    todos_los_errores.append(str(archivo))
                return f"ERROR {archivo} {e}"

        print(f"[INFO] Escaneando archivos en {origen}...")
        archivos_a_procesar = list(Path(origen).rglob("*"))
        
        with open(log_path, "w", encoding="utf-8") as log:
            registrar(log, f"Iniciando escaneo de {len(archivos_a_procesar)} elementos")
            
            # Usar ThreadPoolExecutor para paralelizar la copia
            # El número de hilos se puede ajustar, 8-16 suele ser bueno para I/O
            with ThreadPoolExecutor(max_workers=10) as executor:
                resultados = list(executor.map(proceso_archivo, archivos_a_procesar))
                
                for res in resultados:
                    if res:
                        registrar(log, res)

            if errores:
                with open(err_path, "w", encoding="utf-8") as f_err:
                    json.dump(todos_los_errores, f_err, indent=4)

        print(f"[INFO] Tarea '{nombre}' finalizada: {copiados} copiados, {omitidos} omitidos, {len(todos_los_errores)} errores.")
        print(f"[INFO] Tiempo invertido: {time.time() - inicio:.2f}s")

        return err_path, bool(errores), total_bytes_copiados

    except Exception as e:
        print(f"[ERROR] Fallo general en la copia de archivos: {e}")
        return None, False, 0

def calcular_espacio_necesario(origen, destino, dias=None, solo_qvd=False):
    try:
        total = 0
        nuevos = 0
        modificados = 0
        fecha_actual = datetime.now()
        
        for archivo in Path(origen).rglob("*"):
            if not validar_archivo(archivo, solo_qvd, dias, fecha_actual):
                continue

            destino_ruta = os.path.join(destino, os.path.relpath(archivo, origen))
            size = archivo.stat().st_size

            if os.path.exists(destino_ruta):
                size_dest = os.path.getsize(destino_ruta)
                if size != size_dest:
                    total += max(size - size_dest, 0)
                    modificados += 1
            else:
                total += size
                nuevos += 1

        return {
            "bytes": total,
            "nuevos": nuevos,
            "modificados": modificados
        }

    except Exception as e:
        print(f"[ERROR] Fallo al calcular espacio necesario: {e}")
        return None