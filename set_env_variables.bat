@echo off
REM Set Databricks environment variables at system level

echo Setting Databricks environment variables...
echo.

REM Set USER environment variables (recommended)
setx DATABRICKS_CATALOG "hackathon"
setx DATABRICKS_SCHEMA "hackathon_ctrl_alt_elite"

echo.
echo Environment variables set:
echo   DATABRICKS_CATALOG=hackathon
echo   DATABRICKS_SCHEMA=hackathon_ctrl_alt_elite
echo.
echo IMPORTANT: Close and reopen your terminal for changes to take effect!
echo.
pause
