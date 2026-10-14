@echo off
REM ============================================================
REM  Local runner - apne PC se profile update karo
REM  Use:  is file par DOUBLE-CLICK karo
REM
REM  SECURITY: token ".env" file me padha jaata hai, jo .gitignore
REM  me listed hai - isliye wo kabhi GitHub par upload nahi hoga.
REM  (setx se token Windows registry me permanently save hota tha,
REM   isliye wo tarika jaan-boojh kar chhoda gaya hai.)
REM ============================================================

echo ==========================================
echo   GitHub Profile Auto-Manager (Local)
echo ==========================================
echo.

cd /d "%~dp0"

REM --- token check ---
if not exist ".env" (
    echo [!] ".env" file nahi mili - token load nahi hoga.
    echo.
    echo     Fix karne ke liye:
    echo     1. Is folder me ek nayi file banao, naam rakho:  .env
    echo        (Notepad me File ^> Save as, phir "All Files" chuno
    echo         aur quotes hatao warna ".env.txt" ban jayega)
    echo     2. Us file me sirf itni ek line likho:
    echo.
    echo        GITHUB_TOKEN=github_pat_xxxxx
    echo.
    echo     3. Apna asli token paste kar do aur save kar do.
    echo.
    echo     Note: ".env" file hidden ho sakti hai. File Explorer me
    echo     View ^> Show ^> Hidden items ON kar lein.
    echo.
    echo     NOTE: Actions me token set kar diya hoga to ye zaroorat
    echo           nahi padegi - sirf Actions se chal jayega.
    echo.
    pause
    exit /b 1
)

echo [OK] .env file mili.
echo.

REM --- python check ---
python --version >nul 2>nul
if errorlevel 1 (
    echo [!] Python nahi mila.
    echo     https://python.org se install karein aur install ke
    echo     dauraan "Add Python to PATH" checkbox ZAROOR ON rakhein.
    echo.
    pause
    exit /b 1
)

echo [OK] Python mil gaya.
echo.

REM --- dry run (kuch nahi badlega) ---
echo --- DRY RUN (preview) ---
echo.
python automation\profile_manager.py --dry-run
if errorlevel 1 (
    echo.
    echo [!] Script me kuch problem aayi - upar ka error dekhein.
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo  Preview upar dikh gaya.
echo.
echo  ASLI update ke liye PowerShell me chalayein:
echo      python automation\profile_manager.py
echo.
echo  (Is file me --dry-run hata kar bhi chalaya ja sakta hai)
echo ==========================================
echo.

pause