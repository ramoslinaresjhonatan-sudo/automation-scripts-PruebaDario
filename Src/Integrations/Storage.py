import os

class Storage:
    def __init__(self):
        self.DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Storage"))
        if not os.path.exists(self.DIR):
            os.makedirs(self.DIR, exist_ok=True)

    def extraer(self):
        try:
            archivos = os.listdir(self.DIR)
            return [os.path.join(self.DIR, f) for f in archivos if os.path.isfile(os.path.join(self.DIR, f))]
        except Exception as e:
            print(f"Error al extraer de Storage: {e}")
            return []

    def extraerListaDeArchivos(self):
        try:
            return os.listdir(self.DIR)
        except:
            return []

    def Eliminar(self, nombre):
        try:
            ruta = os.path.join(self.DIR, nombre)
            if os.path.exists(ruta):
                os.remove(ruta)
                return True
        except Exception as e:
            print(f"Error al eliminar {nombre}: {e}")
        return False

    def eliminarContenidoStorage(self):
        archivos = self.extraer()
        for f in archivos:
            try:
                os.remove(f)
            except:
                pass
        return True