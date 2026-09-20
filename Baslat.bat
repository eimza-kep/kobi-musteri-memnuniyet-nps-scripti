@echo off
chcp 65001 >nul
echo =================================================================
echo        MÜŞTERİ MEMNUNİYETİ VE NPS SİSTEMİ BAŞLATICI
echo =================================================================
echo.
echo Sunucu hazırlanıyor ve başlatılıyor...
echo Port: 8091
echo.
start "" http://localhost:8091
python server.py
pause
