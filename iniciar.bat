@echo off
title YouTube Downloader (1080p)
color 0a

echo ==========================================
echo       Iniciando YouTube Downloader...
echo ==========================================

:: Comprobar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se encontro Python en el sistema.
    echo Por favor, instala Python desde python.org y asegurate de marcar "Add Python to PATH".
    pause
    exit /b
)

:: Crear entorno si no existe
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Configurando el entorno virtual por primera vez...
    echo Esto puede tardar un minuto, por favor espera.
    python -m venv venv
)

:: Activar entorno e instalar/actualizar dependencias
call venv\Scripts\activate.bat
echo [INFO] Verificando dependencias (yt-dlp y ffmpeg)...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt >nul 2>&1

:: Ejecutar script
echo [INFO] Abriendo interfaz...
start pythonw downloader.py
exit
