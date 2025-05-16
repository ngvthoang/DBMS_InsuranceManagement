@echo off
REM This script is used to create a backup of the InsuranceDB database.
REM It generates a timestamped folder in the backup directory and stores the SQL dump of the database.
REM How it works:
REM 1. The script sets up a timestamp to uniquely identify each backup.
REM 2. It creates a new folder in the specified backup directory using the timestamp.
REM 3. The `mysqldump` command is used to export the database into an SQL file within the newly created folder.
REM 4. The database credentials (DB_USER and DB_PASSWORD) are used to authenticate the connection.
REM 
REM How to access and use the backup:
REM 1. Navigate to the backup directory (d:\PythonCode\DBMS_InsuranceManagement\backup) on the local machine.
REM 2. Locate the folder with the desired timestamp.
REM 3. Use the SQL file inside the folder to restore the database if needed.
REM    Example restore command:
REM    mysql -u root -p InsuranceDB < path_to_backup.sql
REM 
REM Use cases:
REM - Disaster recovery: Restore the database in case of data loss or corruption.
REM - Migration: Transfer the database to another server or environment.
REM - Archiving: Keep a historical record of the database state at specific points in time.

:: filepath: d:\PythonCode\DBMS_InsuranceManagement\backup_script.bat
set TIMESTAMP=%date:~-4%-%date:~4,2%-%date:~7,2%_%time:~0,2%-%time:~3,2%
set BACKUP_DIR=d:\PythonCode\DBMS_InsuranceManagement\backup
set DB_NAME=InsuranceDB
set DB_USER=root
set DB_PASSWORD=your_password

mkdir %BACKUP_DIR%\%TIMESTAMP%
mysqldump -u %DB_USER% -p%DB_PASSWORD% %DB_NAME% > %BACKUP_DIR%\%TIMESTAMP%\%DB_NAME%.sql
