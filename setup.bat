@echo off
setlocal

echo ==========================================
echo   Instalador de Automation Scripts
echo ==========================================

:: Verificar si Python est instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no est instalado o no est en el PATH.
    echo Por favor, instale Python antes de continuar.
    pause
    exit /b 1
)

:: Crear entorno virtual si no existe
if not exist "venv" (
    echo [+] Creando entorno virtual (venv)...
    python -m venv venv
) else (
    echo [!] El entorno virtual ya existe.
    echo [+] Actualizando dependencias en el entorno existente...
)

:: Activar entorno virtual e instalar dependencias
echo [+] Activando entorno virtual e instalando requerimientos...
call venv\Scripts\activate.bat

echo [+] Actualizando pip...
python -m pip install --upgrade pip

echo [+] Instalando dependencias desde requirement.txt...
pip install -r requirement.txt

:: Instalar Playwright Chromium
echo [+] Instalando dependencias de Playwright (Chromium)...
playwright install chromium

echo ==========================================
echo   Instalacion completada correctamente
echo ==========================================
echo Puede ejecutar los scripts activando el venv:
echo call venv\Scripts\activate
echo ==========================================
pause
