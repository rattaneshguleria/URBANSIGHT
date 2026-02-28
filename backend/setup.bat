@echo off
echo ========================================
echo UrbanSight - Backend Setup
echo ========================================
echo.

echo Step 1: Creating required directories...
mkdir uploads 2>nul
mkdir static\processed 2>nul
echo [OK] Directories created
echo.

echo Step 2: Installing Python packages...
pip install --upgrade pip
pip install -r requirements.txt
echo [OK] Packages installed
echo.

echo Step 3: Verifying installation...
python -c "import cv2; print('OpenCV version:', cv2.__version__)"
echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the server:
echo   python app.py
echo.
echo Then open:
echo   http://localhost:5000
echo.
pause