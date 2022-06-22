@echo off

:: cd to the directory the script is in
@cd %~dp0

:: Check for python 3 installation on system
python --version 3 > nul

if errorlevel == 1 (
	goto installPythonViaChocolatey
) else (
	goto executeMainScript
)

:installPythonViaChocolatey:
	echo Installing chocolatey windows package manager
	@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
	
	echo Installing Python3
	@choco install -y python3

	goto executeMainScript

:executeMainScript
	python install.py %*