@echo off
REM HyperOS 1 Debloat — launcher para Windows
REM Dois cliques aqui abrem a interface grafica.
REM Precisa de Python 3.8+ instalado com "Add Python to PATH".
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    echo Python nao encontrado.
    echo Instale o Python em https://www.python.org/downloads/
    echo Marque "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)
python hyperos_debloat.py
if errorlevel 1 (
    echo.
    echo O programa fechou com erro. Veja a mensagem acima.
    pause
)
