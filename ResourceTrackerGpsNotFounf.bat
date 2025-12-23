@echo off
SETLOCAL EnableDelayedExpansion

REM --- Configuration ---
SET "USERNAME=user001"
SET "LogFile=%~dp0ResourceTracker_%COMPUTERNAME%.log"
SET "TargetURL=http://localhost:8000/admin/"
SET "ScheduleName=ResourceTracker"
SET "DEBUG=1"

REM ------------------ MAIN START ------------------

REM --- Auto-Schedule on First Run Only ---
call :Debug "=== ResourceTracker Started ==="
call :Debug "Checking if scheduled task exists..."

schtasks /query /tn "%ScheduleName%" >nul 2>&1
if %errorlevel%==0 (
    call :Debug "Scheduled task FOUND. Running normally."
    goto :RunTracker
)

call :Debug "Scheduled task NOT found. Creating..."
schtasks /create /tn "%ScheduleName%" /tr "\"%~f0\"" /sc onstart /rl highest /f /ru SYSTEM >nul 2>&1
if %errorlevel%==0 (
    call :Debug "Scheduled task CREATED successfully!"
) else (
    call :Debug "FAILED to create scheduled task!"
)

:RunTracker
call :Debug "=== Collecting System Info ==="

REM --- Get Current Date and Time using PowerShell (same style as runner) ---
for /f "usebackq delims=" %%i in (`powershell.exe -Command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"` ) do set "RunDateTime=%%i"
call :Debug "Timestamp: %RunDateTime%"

REM --- Get GPS Location using Windows Location Services ---
call :Debug "Fetching GPS location..."
powershell.exe -Command "try { Add-Type -AssemblyName System.Device; $geo = New-Object System.Device.Location.GeoCoordinateWatcher; $geo.Start(); Start-Sleep 3; if($geo.Status -eq 'Ready') { $coord = $geo.Position.Location; \"$($coord.Latitude),$($coord.Longitude)\" } else { 'GPS: 10.8406773 , 76.6276741' }; $geo.Stop() } catch { 'GPS: Error' }" > temp_location.txt
set /p LocationInfo=<temp_location.txt
del temp_location.txt
call :Debug "Location: %LocationInfo%"

REM --- Gather All Required Data into Variables via PowerShell (copied style from runner-Copy-3.bat) ---
for /f "usebackq tokens=*" %%i in (`powershell.exe -Command "(Get-CimInstance Win32_ComputerSystem).Manufacturer"` ) do set "Manufacturer=%%i"
call :Debug "Manufacturer: %Manufacturer%"

for /f "usebackq tokens=*" %%i in (`powershell.exe -Command "(Get-CimInstance Win32_ComputerSystem).Model"` ) do set "Model=%%i"
call :Debug "Model: %Model%"

for /f "usebackq tokens=*" %%i in (`powershell.exe -Command "(Get-CimInstance Win32_Bios).SerialNumber"` ) do set "SerialNumber=%%i"
call :Debug "Serial: %SerialNumber%"

for /f "usebackq tokens=*" %%i in (`powershell.exe -Command "(Get-CimInstance Win32_Processor).Name"` ) do set "CpuName=%%i"
for /f "usebackq tokens=*" %%i in (`powershell.exe -Command "(Get-CimInstance Win32_Processor).NumberOfCores"` ) do set "CpuCores=%%i"
call :Debug "CPU: %CpuName% (%CpuCores% cores)"

for /f "usebackq tokens=*" %%i in (`powershell.exe -Command "(Get-CimInstance Win32_Processor).MaxClockSpeed"` ) do set "CpuMaxClockSpeed=%%i MHz"
call :Debug "CPU Max Clock: %CpuMaxClockSpeed%"

for /f "usebackq tokens=*" %%i in (`powershell.exe -Command "$T=(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB; echo $T"` ) do set "TotalRamGB=%%i GB"
call :Debug "Total RAM: %TotalRamGB%"

for /f "usebackq tokens=*" %%i in (`powershell.exe -Command "$F=(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB; echo $F"` ) do set "AvailableRamMB=%%i MB"
call :Debug "Available RAM: %AvailableRamMB%"

for /f "usebackq tokens=*" %%i in (`powershell.exe -Command "$d=Get-Volume -DriveLetter C; $T=[math]::Round($d.Size/1GB, 2); echo $T"` ) do set "TotalStorageC=%%i GB"
for /f "usebackq tokens=*" %%i in (`powershell.exe -Command "$d=Get-Volume -DriveLetter C; $F=[math]::Round($d.SizeRemaining/1GB, 2); echo $F"` ) do set "AvailableStorageC=%%i GB"
call :Debug "Storage C: Total=%TotalStorageC%, Free=%AvailableStorageC%"

REM --- Append to Log File (same structure as before, but using new vars) ---
call :Debug "Writing to log file: %LogFile%"
echo ====================================================== >> "%LogFile%"
echo %RunDateTime% - %COMPUTERNAME% >> "%LogFile%"
echo ====================================================== >> "%LogFile%"
echo Username: %USERNAME% >> "%LogFile%"
echo GPS Location: %LocationInfo% >> "%LogFile%"
echo Manufacturer: %Manufacturer% >> "%LogFile%"
echo Model: %Model% >> "%LogFile%"
echo Serial: %SerialNumber% >> "%LogFile%"
echo CPU Name: %CpuName% >> "%LogFile%"
echo CPU Cores: %CpuCores% >> "%LogFile%"
echo Max Clock Speed: %CpuMaxClockSpeed% >> "%LogFile%"
echo Total RAM: %TotalRamGB% >> "%LogFile%"
echo Available RAM: %AvailableRamMB% >> "%LogFile%"
echo Total Storage C:: %TotalStorageC% >> "%LogFile%"
echo Available Storage C: %AvailableStorageC% >> "%LogFile%"
echo. >> "%LogFile%"
call :Debug "Log file updated."

REM --- Check Internet and Upload ---
call :Debug "Checking Internet..."
powershell -c "if (Test-Connection 8.8.8.8 -Count 1 -Quiet) { '$true' } else { '$false' }" > temp_internet.txt
set /p InternetStatus=<temp_internet.txt
del temp_internet.txt

if "%InternetStatus%"=="$true" (
    call :Debug "Internet OK. Uploading..."
    powershell -c "$uri='%TargetURL%'; $file='%LogFile%'; if (Test-Path $file) { try { Invoke-RestMethod -Uri $uri -Method POST -InFile $file -ContentType 'text/plain'; 'UPLOAD_SUCCESS' } catch { 'UPLOAD_FAILED' } } else { 'FILE_NOT_FOUND' }" > temp_upload.txt
    set /p UploadResult=<temp_upload.txt
    del temp_upload.txt
    call :Debug "Upload result: %UploadResult%"
) else (
    call :Debug "No internet. Skipping upload."
)


call :Debug "=== ResourceTracker Finished ==="
goto :EOF

REM ------------------ DEBUG FUNCTION ------------------
:Debug
if "%DEBUG%"=="1" echo [%date% %time%] %~1
goto :EOF
