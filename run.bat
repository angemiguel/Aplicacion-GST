@echo off
title GSTP - Sistema de Gestion de Pasantias
echo ============================================
echo  POMARAY GSTP - Iniciando Aplicacion
echo ============================================
echo.

REM --- Cargar variables de entorno ---
if exist ".env" (
    for /f "tokens=1,* delims==" %%a in (.env) do set %%a=%%b
)

REM --- Verificar entorno virtual ---
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] No se encuentra el entorno virtual.
    echo Ejecuta primero: setup.bat
    pause
    exit /b 1
)

REM --- Verificar MySQL ---
echo [INFO] Verificando conexion a MySQL...
mysql -u root -pdangel232 -e "SELECT 1;" >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] MySQL no responde.
    echo Asegurate de que el servicio MySQL/MariaDB este iniciado.
    echo.
    choice /c sn /m "Intentar iniciar el servicio"
    if errorlevel 2 goto :skip_mysql
    net start MySQL 2>nul || net start MariaDB 2>nul || echo [AVISO] No se pudo iniciar automaticamente
    :skip_mysql
)

REM --- Iniciar aplicacion ---
echo.
echo [OK] Iniciando servidor...
echo.
echo  Abre tu navegador en: http://127.0.0.1:5000
echo  Presiona CTRL+C para detener el servidor
echo.
call venv\Scripts\activate.bat && python app.py

echo.
echo Servidor detenido.
pause
