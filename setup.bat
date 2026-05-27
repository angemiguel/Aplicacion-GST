@echo off
title GSTP - Instalacion
echo ============================================
echo  POMARAY GSTP - Configuracion Inicial
echo ============================================
echo.

REM --- Verificar Python ---
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado.
    echo Descargalo desde: https://www.python.org/downloads/
    echo Marca "Add Python to PATH" durante la instalacion.
    pause
    exit /b 1
)
echo [OK] Python detectado
python --version

REM --- Verificar MySQL ---
mysql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] MySQL no esta en el PATH.
    echo Asegurate de tener MySQL/MariaDB instalado y corriendo.
    echo Descarga: https://dev.mysql.com/downloads/installer/
    echo.
    set /p MYSQL_OK=Continuar de todas formas? (s/n): 
    if /i "!MYSQL_OK!" neq "s" exit /b 1
)
echo [OK] MySQL detectado

REM --- Crear entorno virtual ---
if not exist "venv" (
    echo.
    echo Creando entorno virtual...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
    echo [OK] Entorno virtual creado
) else (
    echo [OK] Entorno virtual ya existe
)

REM --- Activar e instalar dependencias ---
echo.
echo Instalando dependencias...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] No se pudieron instalar las dependencias.
    pause
    exit /b 1
)
echo [OK] Dependencias instaladas

REM --- Configurar base de datos ---
echo.
echo ============================================
echo  Configuracion de Base de Datos
echo ============================================
echo.
set /p DB_USER=Usuario MySQL (default: root): 
if "%DB_USER%"=="" set DB_USER=root
set /p DB_PASS=Contrasena MySQL: 
set /p DB_NAME=Nombre BD (default: base_pasantia_db): 
if "%DB_NAME%"=="" set DB_NAME=base_pasantia_db

echo.
echo Creando base de datos...
mysql -u %DB_USER% -p%DB_PASS% -e "CREATE DATABASE IF NOT EXISTS %DB_NAME%;" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo conectar a MySQL. Verifica credenciales.
    echo Puedes configurarlo manualmente despues en app.py linea 15.
    pause
    exit /b 1
)
echo [OK] Base de datos lista

REM --- Guardar configuracion en .env ---
echo.
echo Guardando configuracion...
(
    echo DATABASE_URL=mysql://%DB_USER%:%DB_PASS%@localhost/%DB_NAME%
    echo SECRET_KEY=pomaray_2026_gst
    echo IMGBB_API_KEY=0e6901cb0c02a5f295b89eff4e86a61e
    echo DEFAULT_ADMIN_PASSWORD=123
) > .env
echo [OK] Configuracion guardada en .env

REM --- Inicializar tablas y admin ---
echo.
echo Inicializando tablas y usuario admin...
call venv\Scripts\python.exe -c "
import os
os.environ['DATABASE_URL'] = 'mysql://%DB_USER%:%DB_PASS%@localhost/%DB_NAME%'
from app import app, db, Usuario
from werkzeug.security import generate_password_hash
with app.app_context():
    db.create_all()
    if not Usuario.query.filter_by(username='admin').first():
        db.session.add(Usuario(username='admin', password=generate_password_hash('123'), rol='admin'))
        db.session.commit()
        print('Admin creado: admin / 123')
"
echo [OK] Base de datos inicializada

echo.
echo ============================================
echo  Instalacion completada con exito
echo ============================================
echo.
echo Para iniciar la aplicacion, ejecuta: run.bat
echo Usuario admin: admin / 123
echo.
pause
