@echo off
setlocal enabledelayedexpansion
title VaccineTransport IoT — Configurar Novo PC
color 0A

echo ================================================================
echo  VaccineTransport IoT — Configurador de Novo PC
echo ================================================================
echo.
echo  O que este script faz automaticamente:
echo    1. Cria o arquivo .env (credenciais da aplicacao)
echo    2. Atualiza IP e caminhos em todos os arquivos do projeto
echo    3. Regenera os certificados TLS (requer Git for Windows)
echo    4. Atualiza o certificado CA no firmware do ESP32
echo    5. Cria o ambiente Python (venv) e instala dependencias
echo    6. Inicializa o datadir do MySQL (se necessario)
echo.
echo  PRE-REQUISITOS — instale ANTES de rodar este script:
echo    Python 3.11+      https://python.org/downloads/
echo                      (marque "Add Python to PATH"^)
echo    Git for Windows   https://git-scm.com/download/win
echo    MySQL 8.0         https://dev.mysql.com/downloads/mysql/
echo    Mosquitto         https://mosquitto.org/download/
echo    Arduino IDE       https://www.arduino.cc/en/software
echo.
echo  Pressione qualquer tecla para comecar ou feche para cancelar.
pause >nul
echo.

:: ================================================================
:: Detectar ambiente atual
:: ================================================================

set "PROJECT_DIR=%~dp0"
if "!PROJECT_DIR:~-1!"=="\" set "PROJECT_DIR=!PROJECT_DIR:~0,-1!"
set "NEW_USER=%USERNAME%"
set "MYSQL_DATA=C:\Users\!NEW_USER!\mysql-data"
set "MYSQL_DATA_FWD=C:/Users/!NEW_USER!/mysql-data"

:: Detectar IP local via PowerShell (evita problemas de aspas no for/f)
> "%TEMP%\vt_ip.ps1" echo (Get-NetIPAddress -AddressFamily IPv4 ^| Where-Object { $_.PrefixOrigin -eq 'Dhcp' -or $_.PrefixOrigin -eq 'Manual' } ^| Select-Object -First 1 -ExpandProperty IPAddress)
for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP%\vt_ip.ps1"') do set "NEW_IP=%%i"
del "%TEMP%\vt_ip.ps1" 2>nul
if not defined NEW_IP set "NEW_IP=127.0.0.1"

:: Caminho do projeto com forward slashes
> "%TEMP%\vt_fwd.ps1" echo ('!PROJECT_DIR!').Replace('\', '/')
for /f "delims=" %%i in ('powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP%\vt_fwd.ps1"') do set "PROJECT_FWD=%%i"
del "%TEMP%\vt_fwd.ps1" 2>nul

echo  Configuracao detectada:
echo    IP da maquina   : !NEW_IP!
echo    Usuario Windows : !NEW_USER!
echo    Pasta do projeto: !PROJECT_DIR!
echo    MySQL datadir   : !MYSQL_DATA!
echo.
set /p "CONFIRM=Tudo certo? Deseja continuar? (S/N): "
if /i not "!CONFIRM!"=="S" ( echo. & echo Cancelado. & pause & exit /b 0 )
echo.

:: ================================================================
:: PASSO 1 — Criar .env se nao existir (gitignored, nao vem do repo)
:: ================================================================
echo [1/6] Criando arquivo .env...

set "DOTENV=!PROJECT_DIR!\source\app\.env"
if exist "!DOTENV!" (
    echo  .env ja existe — mantido sem alteracao.
) else (
    echo  Criando .env com configuracoes padrao...
    > "!DOTENV!" echo DB_HOST=127.0.0.1
    >> "!DOTENV!" echo DB_USER=root
    >> "!DOTENV!" echo DB_PASSWORD=VaccineSecure@2026
    >> "!DOTENV!" echo DB_NAME=vaccine_transport
    >> "!DOTENV!" echo.
    >> "!DOTENV!" echo FLASK_SECRET_KEY=v@ccine-iot-tcc-secret-2026-xK9mPqR7
    >> "!DOTENV!" echo.
    >> "!DOTENV!" echo MQTT_BROKER=127.0.0.1
    >> "!DOTENV!" echo MQTT_PORT=8883
    >> "!DOTENV!" echo MQTT_CA_CERT=!PROJECT_FWD!/certs/ca.crt
    >> "!DOTENV!" echo MQTT_USERNAME=flask-subscriber
    >> "!DOTENV!" echo MQTT_PASSWORD=FlaskMqtt@2026
    >> "!DOTENV!" echo.
    >> "!DOTENV!" echo BACKUP_GPG_PASSPHRASE=Backup@htzFlDiYdvfOW8Ddy44NhLrB
    >> "!DOTENV!" echo BACKUP_LOCAL_DIR=!PROJECT_FWD!/backups
    >> "!DOTENV!" echo BACKUP_ONEDRIVE_DIR=C:/Users/!NEW_USER!/OneDrive/VaccineTransport_Backups
    >> "!DOTENV!" echo BACKUP_KEEP_DAYS=30
    echo  .env criado.
)

:: ================================================================
:: PASSO 2 — Atualizar IP e caminhos em todos os arquivos
:: ================================================================
echo.
echo [2/6] Atualizando IP e caminhos nos arquivos do projeto...

set "CFG_PS1=%TEMP%\vt_cfg.ps1"
if exist "!CFG_PS1!" del "!CFG_PS1!"

>> "!CFG_PS1!" echo $proj    = '!PROJECT_DIR!'
>> "!CFG_PS1!" echo $projFwd = '!PROJECT_FWD!'
>> "!CFG_PS1!" echo $ip      = '!NEW_IP!'
>> "!CFG_PS1!" echo $user    = '!NEW_USER!'
>> "!CFG_PS1!" echo $mysql   = '!MYSQL_DATA_FWD!'
>> "!CFG_PS1!" echo.
>> "!CFG_PS1!" echo function Rep($f, $p, $r) {
>> "!CFG_PS1!" echo     if (-not (Test-Path $f)) { Write-Host ('  SKIP: ' + (Split-Path $f -Leaf)); return }
>> "!CFG_PS1!" echo     $c = [IO.File]::ReadAllText($f)
>> "!CFG_PS1!" echo     $n = $c -replace $p, $r
>> "!CFG_PS1!" echo     if ($n -ne $c) { [IO.File]::WriteAllText($f, $n) }
>> "!CFG_PS1!" echo     Write-Host ('  OK: ' + (Split-Path $f -Leaf))
>> "!CFG_PS1!" echo }
>> "!CFG_PS1!" echo.
>> "!CFG_PS1!" echo Write-Host '  Substituindo IP do servidor...'
>> "!CFG_PS1!" echo Rep "$proj\source\esp32\main\main.ino" '\b\d+\.\d+\.\d+\.\d+\b' $ip
>> "!CFG_PS1!" echo Rep "$proj\certs\gerar_certs.sh"       '\b\d+\.\d+\.\d+\.\d+\b' $ip
>> "!CFG_PS1!" echo Rep "$proj\iniciar.bat"                '\b\d+\.\d+\.\d+\.\d+\b' $ip
>> "!CFG_PS1!" echo.
>> "!CFG_PS1!" echo Write-Host '  Substituindo caminhos do projeto (forward slashes)...'
>> "!CFG_PS1!" echo $oldF = '[A-Za-z]:/Users/[^/]+/[^/]+/vaccine-transport-iot'
>> "!CFG_PS1!" echo Rep "$proj\source\broker\mosquitto-tls.conf" $oldF $projFwd
>> "!CFG_PS1!" echo Rep "$proj\source\app\.env"                  $oldF $projFwd
>> "!CFG_PS1!" echo Rep "$proj\certs\gerar_certs.sh"             $oldF $projFwd
>> "!CFG_PS1!" echo.
>> "!CFG_PS1!" echo Write-Host '  Substituindo caminhos do projeto (backslashes no iniciar.bat)...'
>> "!CFG_PS1!" echo $oldB = '[A-Za-z]:\\Users\\[^\\]+\\[^\\]+\\vaccine-transport-iot'
>> "!CFG_PS1!" echo Rep "$proj\iniciar.bat" $oldB $proj
>> "!CFG_PS1!" echo.
>> "!CFG_PS1!" echo Write-Host '  Atualizando username (mysql-data, OneDrive)...'
>> "!CFG_PS1!" echo Rep "$proj\source\app\.env" 'C:/Users/[^/]+/mysql-data'   $mysql
>> "!CFG_PS1!" echo Rep "$proj\source\app\.env" 'C:/Users/[^/]+/OneDrive'     "C:/Users/$user/OneDrive"
>> "!CFG_PS1!" echo Rep "$proj\iniciar.bat"     'C:/Users/[^/]+/mysql-data'   $mysql
>> "!CFG_PS1!" echo Rep "$proj\iniciar.bat"     'C:\\Users\\[^\\]+\\mysql-data'  "C:\Users\$user\mysql-data"
>> "!CFG_PS1!" echo.
>> "!CFG_PS1!" echo Write-Host '  Concluido.'

powershell -NoProfile -ExecutionPolicy Bypass -File "!CFG_PS1!"
if !errorlevel! neq 0 (
    echo [ERRO] Falha ao atualizar arquivos.
    del "!CFG_PS1!" 2>nul
    pause & exit /b 1
)
del "!CFG_PS1!" 2>nul

:: ================================================================
:: PASSO 3 — Regenerar certificados TLS
:: ================================================================
echo.
echo [3/6] Regenerando certificados TLS...

set "GITBASH=C:\Program Files\Git\bin\bash.exe"
if not exist "!GITBASH!" (
    echo  [AVISO] Git Bash nao encontrado: !GITBASH!
    echo  Instale Git for Windows e depois execute manualmente:
    echo    cd certs ^&^& bash gerar_certs.sh
    echo  E depois atualize manualmente o CA_CERT no main.ino.
    goto :SKIP_CERTS
)

echo  Rodando gerar_certs.sh via Git Bash...
set MSYS_NO_PATHCONV=1
"!GITBASH!" -c "cd '!PROJECT_FWD!/certs' && bash gerar_certs.sh 2>&1"
if !errorlevel! neq 0 (
    echo  [ERRO] Falha ao gerar certificados. Execute manualmente:
    echo    cd certs ^&^& bash gerar_certs.sh
    goto :SKIP_CERTS
)
echo  Certificados gerados com sucesso.

:: ================================================================
:: PASSO 4 — Atualizar CA cert no firmware do ESP32
:: ================================================================
echo.
echo [4/6] Atualizando CA cert no firmware (main.ino)...

set "CA_PS1=%TEMP%\vt_ca.ps1"
if exist "!CA_PS1!" del "!CA_PS1!"

>> "!CA_PS1!" echo $caPath  = '!PROJECT_DIR!\certs\ca.crt'
>> "!CA_PS1!" echo $inoPath = '!PROJECT_DIR!\source\esp32\main\main.ino'
>> "!CA_PS1!" echo if (-not (Test-Path $caPath)) { Write-Host '  ca.crt nao encontrado — pulando.'; exit }
>> "!CA_PS1!" echo $ca  = (Get-Content $caPath -Raw).TrimEnd()
>> "!CA_PS1!" echo $ino = [IO.File]::ReadAllText($inoPath)
>> "!CA_PS1!" echo $pat = '(?s)static const char CA_CERT\[\] PROGMEM = R"EOF\(.*?\)EOF";'
>> "!CA_PS1!" echo $rep = 'static const char CA_CERT[] PROGMEM = R"EOF(' + "`n" + $ca + "`n" + ')EOF";'
>> "!CA_PS1!" echo $new = $ino -replace $pat, $rep
>> "!CA_PS1!" echo [IO.File]::WriteAllText($inoPath, $new)
>> "!CA_PS1!" echo Write-Host '  main.ino atualizado com novo CA cert.'

powershell -NoProfile -ExecutionPolicy Bypass -File "!CA_PS1!"
del "!CA_PS1!" 2>nul

goto :AFTER_CERTS

:SKIP_CERTS
echo  [AVISO] Certificados NAO regenerados. Passos 3 e 4 pulados.

:AFTER_CERTS
echo.
echo  LEMBRETE: Importe o novo ca.crt no navegador como CA confiavel:
echo    Arquivo: !PROJECT_DIR!\certs\ca.crt
echo    Chrome: chrome://settings/security ^> Gerenciar certificados
echo            ^> Autoridades ^> Importar ^> selecionar ca.crt

:: ================================================================
:: PASSO 5 — Ambiente Python (venv + dependencias)
:: ================================================================
echo.
echo [5/6] Configurando ambiente Python...

where python >nul 2>&1
if !errorlevel! neq 0 (
    echo  [AVISO] Python nao encontrado no PATH.
    echo  Instale em https://python.org/downloads/ e marque "Add Python to PATH"
    goto :SKIP_PYTHON
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  !%%v! encontrado.

set "VENV=!PROJECT_DIR!\source\venv"
if not exist "!VENV!\Scripts\python.exe" (
    echo  Criando venv...
    python -m venv "!VENV!"
    if !errorlevel! neq 0 ( echo  [ERRO] Falha ao criar venv. & goto :SKIP_PYTHON )
)
echo  Instalando dependencias...
"!VENV!\Scripts\python.exe" -m pip install -q --upgrade pip 2>nul
"!VENV!\Scripts\python.exe" -m pip install -r "!PROJECT_DIR!\source\app\requirements.txt"
if !errorlevel! neq 0 ( echo  [ERRO] Falha ao instalar dependencias. ) else ( echo  Dependencias OK. )

:SKIP_PYTHON

:: ================================================================
:: PASSO 6 — MySQL datadir
:: ================================================================
echo.
echo [6/6] Verificando MySQL...

set "MYSQLD=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqld.exe"
set "MYSQL_CLI=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"

if not exist "!MYSQLD!" (
    echo  [AVISO] MySQL nao encontrado.
    echo  Instale em https://dev.mysql.com/downloads/mysql/ (versao 8.0^)
    goto :SKIP_MYSQL
)

if not exist "!MYSQL_DATA!\mysql" (
    echo  Inicializando datadir em !MYSQL_DATA!...
    if not exist "!MYSQL_DATA!" mkdir "!MYSQL_DATA!"
    "!MYSQLD!" --initialize-insecure --datadir="!MYSQL_DATA_FWD!"
    if !errorlevel! neq 0 ( echo  [ERRO] Falha ao inicializar datadir. & goto :SKIP_MYSQL )
    echo  datadir inicializado.
) else (
    echo  datadir ja existe em !MYSQL_DATA! — OK
)

:SKIP_MYSQL

:: ================================================================
:: RESULTADO FINAL
:: ================================================================
echo.
echo ================================================================
echo  CONFIGURACAO CONCLUIDA — IP: !NEW_IP!
echo ================================================================
echo.
echo  PROXIMOS PASSOS (em ordem):
echo  ────────────────────────────────────────────────────────────
echo.
echo  1. Execute iniciar.bat para subir MySQL + Mosquitto + Flask
echo.
echo  2. Importe o schema MySQL (apenas na primeira vez):
echo     Abra um novo terminal e execute:
echo     "!MYSQL_CLI!" -u root vaccine_transport ^< "!PROJECT_DIR!\source\database\db_script.sql"
echo     (se der erro de banco nao existe, crie antes: mysql -u root -e "CREATE DATABASE vaccine_transport;"^)
echo.
echo  3. Importe o CA cert no navegador:
echo     Arquivo: !PROJECT_DIR!\certs\ca.crt
echo     Chrome: chrome://settings/security ^> Gerenciar certificados
echo             ^> Autoridades ^> Importar ^> selecionar ca.crt
echo.
echo  4. Arduino IDE — instale as bibliotecas (Tools ^> Manage Libraries^):
echo     - PubSubClient         (Nick O'Leary^)
echo     - ArduinoJson          (Benoit Blanchon^)
echo     - DHT sensor library   (Adafruit^)
echo     - TinyGPSPlus          (Mikal Hart^)
echo     - Adafruit Unified Sensor
echo.
echo  5. Abra source\esp32\main\main.ino no Arduino IDE:
echo     - Atualize o WiFi SSID e senha (linhas WIFI_SSID / WIFI_PASS^)
echo     - Grave no ESP32
echo.
echo  Dashboard: https://!NEW_IP!:5000
echo  Login: admin@vaccine.iot / admin123
echo ================================================================
echo.
pause
