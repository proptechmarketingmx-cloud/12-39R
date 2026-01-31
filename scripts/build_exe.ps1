<#
PowerShell script para construir el EXE de Windows usando PyInstaller.

Uso:
  Ejecutar desde la raíz del repo (PowerShell):
    & .venv\Scripts\Activate.ps1
    .\scripts\build_exe.ps1

Este script crea un ejecutable en `dist\CRMInmobiliario.exe`.
#>

Set-StrictMode -Version Latest

Write-Host "Activando entorno virtual..." -ForegroundColor Cyan
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .venv\Scripts\Activate.ps1
} else {
    Write-Warning "No se encontró .venv. Asegúrate de activar tu entorno virtual manualmente.";
}

Write-Host "Instalando PyInstaller (si es necesario)..." -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install pyinstaller

Write-Host "Limpiando builds previos..." -ForegroundColor Cyan
if (Test-Path "build") { Remove-Item -Recurse -Force build }
if (Test-Path "dist") { Remove-Item -Recurse -Force dist }
if (Test-Path "*.spec") { Get-ChildItem -Filter "*.spec" | Remove-Item -Force }

$exeName = "CRMInmobiliario"

Write-Host "Ejecutando PyInstaller..." -ForegroundColor Green
# Ajusta --add-data según sea necesario. En Windows la sintaxis es 'src;dest'.
# Ejemplo para incluir carpetas estáticas (si existen):
$addData = @()
if (Test-Path "static") { $addData += "static;static" }
if (Test-Path "database\\seeds") { $addData += "database\\seeds;database\\seeds" }

$addDataArgs = $addData | ForEach-Object { "--add-data `"$_`"" } | Out-String

$pyCmd = "pyinstaller --onefile --windowed --name $exeName main.py $addDataArgs"
Write-Host $pyCmd
Invoke-Expression $pyCmd

if (Test-Path "dist\$exeName.exe") {
    Write-Host "Build completado: dist\$exeName.exe" -ForegroundColor Green
} else {
    Write-Host "Build falló. Revisa la salida de pyinstaller." -ForegroundColor Red
}
