@echo off
echo ==============================================
echo   Skill Matrix App - PyInstaller Build Script
echo ==============================================

echo [1/4] Cleaning up old builds...
rmdir /s /q build dist 2>nul
del /q *.spec 2>nul

echo [2/4] Installing necessary requirements...
pip install pyinstaller waitress

echo [3/4] Building the executable (this may take a minute)...
REM We use --onefile to compile to a single executable.
REM We add templates and static folders to the bundle.
REM We explicitly tell PyInstaller to include waitress, bcrypt, and sqlalchemy.
pyinstaller --name "SkillMatrix" --onefile ^
    --add-data "app/templates;app/templates" ^
    --add-data "app/static;app/static" ^
    --hidden-import "bcrypt" ^
    --hidden-import "sqlalchemy" ^
    --hidden-import "waitress" ^
    run.py

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Build failed! Check the output above for details.
    pause
    exit /b %ERRORLEVEL%
)

echo [4/4] Creating distribution folder...
mkdir dist\SkillMatrixApp
move dist\SkillMatrix.exe dist\SkillMatrixApp\
copy skill_assessment.db dist\SkillMatrixApp\

echo ==============================================
echo   BUILD COMPLETE!
echo ==============================================
echo.
echo Your final standalone app is located at:
echo   dist\SkillMatrixApp\
echo.
echo It contains exactly two files:
echo   - SkillMatrix.exe
echo   - skill_assessment.db
echo.
pause
