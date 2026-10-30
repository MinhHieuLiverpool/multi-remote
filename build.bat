@echo off
title Building Multi Remote Desktop (.exe)
cd /d "%~dp0"
echo =======================================================
echo   Starting Multi Remote Desktop .EXE Build Process
echo =======================================================
python build_exe.py
pause

