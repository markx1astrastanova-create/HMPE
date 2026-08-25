@echo off
setlocal

echo ========================================
echo AUTO PUSH GITHUB - HMPE
echo ========================================
echo.

set /p message="Masukkan pesan commit: "

if "%message%"=="" (
    echo [ERROR] Pesan commit tidak boleh kosong!
    pause
    exit /b
)

echo.
echo [*] Menambahkan file yang berubah (git add .)
git add .

echo.
echo [*] Melakukan commit (git commit -m "%message%")
git commit -m "%message%"

echo.
echo [*] Mengirim ke GitHub (git push origin master)
git push origin master

echo.
echo ========================================
echo PROSES SELESAI
echo ========================================
pause
