@echo off
title Iniciando Automacao CTAR
echo Iniciando a Automacao CTAR...
python main.py
if %errorlevel% neq 0 (
    echo.
    echo Ocorreu um erro ao iniciar a aplicacao usando o Python local.
    echo Certifique-se de que o Python esta instalado e adicionado ao PATH.
    pause
)
