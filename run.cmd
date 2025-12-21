@echo off
REM Wrapper para aceitar "run streamlit app.py" no Windows CMD
REM Uso: run streamlit app.py
setlocal
if /I "%1"=="streamlit" (
  shift
  if "%1"=="" (
    echo Uso: run streamlit <arquivo.py> [--server.headless=false ...]
    exit /b 1
  )
  REM Chama o streamlit via python para garantir o ambiente virtual
  python -m streamlit run %*
) else (
  REM Repassa para qualquer outro comando
  %*
)
