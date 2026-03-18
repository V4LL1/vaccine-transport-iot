@echo off
:: setup_backup_task.bat
:: Registra o backup diario no Windows Task Scheduler
:: Execute como Administrador

setlocal

set PROJECT_DIR=C:\Users\guilh\Desktop\vaccine-transport-iot
set PYTHON=%PROJECT_DIR%\source\venv\Scripts\python.exe
set SCRIPT=%PROJECT_DIR%\source\scripts\backup.py
set TASK_NAME=VaccineTransport_Backup

echo ============================================
echo  Configurando Task Scheduler para backup
echo ============================================

:: Remove task anterior se existir
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

:: Cria task diaria as 02:00
schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "\"%PYTHON%\" \"%SCRIPT%\"" ^
  /sc DAILY ^
  /st 02:00 ^
  /ru "%USERNAME%" ^
  /rl HIGHEST ^
  /f

if %ERRORLEVEL% == 0 (
    echo [OK] Task criada: backup diario as 02:00
    echo [OK] Executando backup agora para testar...
    echo.
    "%PYTHON%" "%SCRIPT%"
    if %ERRORLEVEL% == 0 (
        echo.
        echo [OK] Backup de teste concluido com sucesso!
        echo      Local:    %PROJECT_DIR%\backups\
        echo      OneDrive: C:\Users\guilh\OneDrive\VaccineTransport_Backups\
    ) else (
        echo [ERRO] Backup de teste falhou. Verifique o log em:
        echo        %PROJECT_DIR%\backups\backup.log
    )
) else (
    echo [ERRO] Falha ao criar task. Execute como Administrador.
)

echo.
pause
