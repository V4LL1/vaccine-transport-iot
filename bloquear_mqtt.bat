@echo off
setlocal EnableDelayedExpansion
title Bloquear MQTT — HiveMQ

:: ── Verifica privilégios de administrador ──────────────────────────────────
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requer privilegios de administrador. Elevando...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"%~f0\"' -Verb RunAs"
    exit /b
)

set "PS1=%TEMP%\bloquear_hivemq_%RANDOM%.ps1"

:: ── Gera o script PowerShell no temp ───────────────────────────────────────
> "%PS1%"  echo Add-Type -TypeDefinition @'
>> "%PS1%" echo using System;
>> "%PS1%" echo using System.Runtime.InteropServices;
>> "%PS1%" echo using System.Diagnostics;
>> "%PS1%" echo public class WinCtrl {
>> "%PS1%" echo     [DllImport("kernel32.dll")]
>> "%PS1%" echo     public static extern bool SetConsoleCtrlHandler(HandlerDelegate h, bool add);
>> "%PS1%" echo     public delegate bool HandlerDelegate(uint t);
>> "%PS1%" echo     public static HandlerDelegate _h;
>> "%PS1%" echo     public static bool Cleanup(uint t) {
>> "%PS1%" echo         try {
>> "%PS1%" echo             var psi = new ProcessStartInfo("netsh", "advfirewall firewall delete rule name=BlockHiveMQ");
>> "%PS1%" echo             psi.CreateNoWindow = true;
>> "%PS1%" echo             psi.UseShellExecute = false;
>> "%PS1%" echo             var p = Process.Start(psi);
>> "%PS1%" echo             if (p != null) p.WaitForExit(4000);
>> "%PS1%" echo         } catch { }
>> "%PS1%" echo         return false;
>> "%PS1%" echo     }
>> "%PS1%" echo }
>> "%PS1%" echo '@
>> "%PS1%" echo.
>> "%PS1%" echo $mi = [WinCtrl].GetMethod("Cleanup", [System.Reflection.BindingFlags]"Public,Static")
>> "%PS1%" echo [WinCtrl]::_h = [Delegate]::CreateDelegate([WinCtrl+HandlerDelegate], $mi)
>> "%PS1%" echo [WinCtrl]::SetConsoleCtrlHandler([WinCtrl]::_h, $true) ^| Out-Null
>> "%PS1%" echo.
>> "%PS1%" echo # Remover regra anterior (evita duplicata) e adicionar
>> "%PS1%" echo netsh advfirewall firewall delete rule name=BlockHiveMQ ^| Out-Null
>> "%PS1%" echo netsh advfirewall firewall add rule name=BlockHiveMQ dir=out action=block protocol=TCP remoteport=8883 ^| Out-Null
>> "%PS1%" echo.
>> "%PS1%" echo Write-Host ''
>> "%PS1%" echo Write-Host '================================================' -ForegroundColor Red
>> "%PS1%" echo Write-Host '   MQTT BLOQUEADO  —  HiveMQ inacessivel' -ForegroundColor Red
>> "%PS1%" echo Write-Host '================================================' -ForegroundColor Red
>> "%PS1%" echo Write-Host ''
>> "%PS1%" echo Write-Host '  ESP32 e Flask perderao conexao com o broker.' -ForegroundColor Yellow
>> "%PS1%" echo Write-Host ''
>> "%PS1%" echo Write-Host '  >> Feche esta janela OU pressione ENTER' -ForegroundColor Cyan
>> "%PS1%" echo Write-Host '     para restaurar a comunicacao.' -ForegroundColor Cyan
>> "%PS1%" echo Write-Host ''
>> "%PS1%" echo $null = Read-Host
>> "%PS1%" echo.
>> "%PS1%" echo netsh advfirewall firewall delete rule name=BlockHiveMQ ^| Out-Null
>> "%PS1%" echo Write-Host ''
>> "%PS1%" echo Write-Host 'Comunicacao MQTT restaurada.' -ForegroundColor Green
>> "%PS1%" echo Start-Sleep -Seconds 2

:: ── Executa e limpa ────────────────────────────────────────────────────────
powershell -NoProfile -ExecutionPolicy Bypass -File "%PS1%"

:: Segurança extra: garantir remoção mesmo que o PS1 falhe
netsh advfirewall firewall delete rule name=BlockHiveMQ >nul 2>&1

del "%PS1%" 2>nul
