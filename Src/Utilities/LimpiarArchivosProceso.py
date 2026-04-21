import os
import glob
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class LimpiadorLogs:

    def __init__(self):
        self.total = 0
        self.espacio = 0
        self.archivos_eliminados = []

    def calcular_fecha(self, limite, tipo):
        ahora = datetime.now()

        if tipo == "dias":
            return ahora - timedelta(days=limite)
        if tipo == "semanas":
            return ahora - timedelta(weeks=limite)
        if tipo == "meses":
            return ahora - relativedelta(months=limite)
        if tipo == "años":
            return ahora - relativedelta(years=limite)

        return ahora

    def limpiar(self, config, logger):
        self.total = 0
        self.espacio = 0
        self.archivos_eliminados = []
        
        fecha_limite = self.calcular_fecha(config["limite"], config["tipo_limite"])

        for ruta in config["rutas_logs"]:
            self._procesar_ruta(ruta, config["extensiones"], fecha_limite, logger)

        return self.total, self.espacio, self.archivos_eliminados

    def _procesar_ruta(self, ruta, extensiones, fecha_limite, logger):
        if not os.path.exists(ruta):
            logger(f"[ERROR] Ruta no existe: {ruta}")
            return

        for root, _, _ in os.walk(ruta):
            for ext in extensiones:
                self._procesar_extension(root, ext, fecha_limite, logger)

    def _procesar_extension(self, root, ext, fecha_limite, logger):
        archivos = glob.glob(os.path.join(root, f"*{ext}"))

        for archivo in archivos:
            if self._debe_eliminar(archivo, fecha_limite):
                self._eliminar(archivo, logger)

    def _debe_eliminar(self, archivo, fecha_limite):
        fecha = datetime.fromtimestamp(os.path.getmtime(archivo))
        return fecha < fecha_limite

    def _eliminar(self, archivo, logger):
        try:
            size = os.path.getsize(archivo)
            os.remove(archivo)

            self.total += 1
            self.espacio += size
            self.archivos_eliminados.append(archivo)

            logger(f"[INFO] Eliminado: {archivo}")
        except Exception as e:
            logger(f"[ERROR] Fallo al eliminar: {archivo} -> {e}")