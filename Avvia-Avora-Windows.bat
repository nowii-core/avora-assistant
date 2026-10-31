@echo off
setlocal
cd /d "%~dp0"
set MODE_ARG=
if /i "%~1"=="demo" set MODE_ARG=--demo

where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo Python 3 non e' installato. Provo a installarlo con winget...
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    echo Chiudi e riapri questo file per completare.
    pause
    exit /b 1
  )
)
set PY=python
where python >nul 2>nul || set PY=py

if "%MODE_ARG%"=="" (
  where ollama >nul 2>nul
  if errorlevel 1 (
    echo Per usare i modelli serve Ollama ^(gratuito^). Provo a installarlo con winget...
    winget install -e --id Ollama.Ollama --accept-package-agreements --accept-source-agreements
    where ollama >nul 2>nul
    if errorlevel 1 (
      echo Installazione non riuscita: scarica Ollama da https://ollama.com/download e riavvia questo file.
      echo Intanto parte la modalita' demo.
      set MODE_ARG=--demo
    )
  )
)
if "%MODE_ARG%"=="" (
  curl -fsS http://127.0.0.1:11434/api/tags >nul 2>nul
  if errorlevel 1 start "" /min ollama serve
  timeout /t 3 /nobreak >nul
)
echo Avvio Avora. Il browser si aprira' da solo; la configurazione dei modelli e' guidata.
%PY% run.py %MODE_ARG%
pause
