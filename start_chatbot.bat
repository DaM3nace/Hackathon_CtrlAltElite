@echo off
set DATABRICKS_CATALOG=hackathon
set DATABRICKS_SCHEMA=hackathon_ctrl_alt_elite
echo Starting chatbot with correct environment variables...
echo DATABRICKS_CATALOG=%DATABRICKS_CATALOG%
echo DATABRICKS_SCHEMA=%DATABRICKS_SCHEMA%
echo.
python web_chat.py
