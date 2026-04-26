@echo off
echo Starting Ternary Bonsai server on GPU...
wsl -e ~/start-llama-server.sh
echo.
echo Server running at:
echo   Local:   http://localhost:8080
echo   LAN:     http://172.24.144.157:8080
echo.
echo Test: curl "http://localhost:8080/v1/chat/completions" -H "Content-Type: application/json" -d "{\model\:\Ternary-Bonsai\,\messages\:[{\role\:\user\,\content\:\Hello!\}],\max_tokens\:50}"
pause
