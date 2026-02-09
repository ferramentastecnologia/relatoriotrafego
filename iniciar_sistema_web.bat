@echo off
echo Iniciando Sistema Web de Relatorios...
echo Aguarde, abrindo o navegador em 3 segundos...

start /B python "c:\Users\Juan\Desktop\Antigravity\app.py"

timeout /t 3 >nul
start http://127.0.0.1:5000

echo.
echo Servidor rodando. Nao feche esta janela enquanto usar o sistema.
echo Pressione qualquer tecla para encerrar o servidor.
pause >nul
taskkill /IM python.exe /F
