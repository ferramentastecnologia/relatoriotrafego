@echo off
echo Verificando instalacao do Pandas...
python -m pip install pandas
if %errorlevel% neq 0 (
    echo [ERRO] Nao foi possivel instalar o pandas automaticamente. 
    echo Tente rodar: pip install pandas
) else (
    echo [SUCESSO] Pandas esta pronto para uso!
)
pause
