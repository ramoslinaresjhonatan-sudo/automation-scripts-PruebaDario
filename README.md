# Automation Scripts

**Automation Scripts** es un módulo diseñado para orquestar y ejecutar tareas recurrentes de mantenimiento de carpetas, respaldos de QVDs y limpieza de históricos de logs de forma automática.

## 📂 Estructura del Proyecto

```text
automation-scripts/
├── Config/               # Archivos de configuración en JSON (CopyPages.json, LimpiadorLog.json)
├── Logs/                 # Registros operativos locales de la ejecución de los scripts
├── requirement.txt       # Dependencias necesarias para ejecutar el proyecto
└── Src/
    ├── Integrations/     # Módulos para interactuar con sistemas externos (Correo SmtpClient y WhatsApp Sender vía Playwright)
    ├── Scripts/          # Scripts principales a ejecutar
    └── Utilities/        # Clases de utilidad y utilerías (procesadores de límite de fechas, escaneadores de carpetas)
```

## ⚙️ Principales Scripts (`Src/Scripts/`)

### 1. `CopyPages.py`
Se encarga de sincronizar y copiar de manera segura archivos (principalmente orientados a formatos `.QVD`) desde un origen a un destino.
- **Características**: Verifica el estado de espacio del disco antes de la transferencia, omite archivos intactos (por tamaño), y registra todo en los logs.
- **Configuración**: Se rige por `Config/CopyPages.json`.
- **Notificaciones**: Utiliza las integraciones de Correo y WhatsApp de los resultados exitosos y errores encontrados en el copiado.

### 2. `LimpiarArchivos.py`
Dedicado a limpiar logs obsoletos de las carpetas de proyectos y el servidor con el fin de liberar espacio.
- **Características**: Soporta parámetros de expiración configurables (`tipo_limite`: "dias", "meses", etc.), buscando recursivamente todo tipo de extensiones definidos (`.log`, `.txt`).
- **Configuración**: Lee las reglas desde `Config/LimpiadorLog.json`. 
- **Notificaciones**: Emite la alerta de limpieza concretada informando la cantidad de archivos borrados y el espacio en MB que se ha liberado.

## 🚀 Instalación y Requisitos

1. Asegúrate de estar posicionado en la carpeta raíz `automation-scripts`.
2. Instala los requerimientos:
   ```bash
   pip install -r requirement.txt
   ```
3. Instala los binarios del navegador automatizado (usado para enviar mensajes de WhatsApp Web):
   ```bash
   playwright install chromium
   ```

## 💻 Uso

Cada script está programado de manera funcional para poder ser añadido a un orquestador (como el Programador de Tareas de Windows o cualquier Cron Job). Puedes probar cada uno ejecutándolo independientemente:

```bash
python Src/Scripts/CopyPages.py
python Src/Scripts/LimpiarArchivos.py
```
