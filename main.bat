@echo off

@clear

:: Variables
set GIT_REMOTE_URL=https://github.com/ErtugrulSener/Automation.git

:: cd to the directory the script is in
@cd %~dp0



:: Check for python 3 installation on system
python --version 3 > nul

if %ERRORLEVEL% NEQ 0 (
	goto installPythonViaChocolatey
) else (
	goto skipPythonInstallation
)

:installPythonViaChocolatey:
	echo Installing chocolatey windows package manager
	@"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"
	
	echo Installing Python3 since it's missing
	@choco install -y python3

:skipPythonInstallation



:: Check for git installation on system
git --version > nul

if %ERRORLEVEL% NEQ 0 (
	goto installGit
) else (
	goto skipGitInstallation
)

:installGit:
	echo Installing Git since it's missing
	@choco install -y git

:skipGitInstallation



:: Check if git repo is checked out here already
if not exist Automation\ (
	@SET remote_url_in_folder=hi
	FOR /F %%I IN ('git config --get remote.origin.url') DO @SET "remote_url_in_folder=%%I"
	
	if "%remote_url_in_folder%"=="%GIT_REMOTE_URL%" (
		goto skipFetchingGitRepository
	) else (
		goto fetchGitRepository
	)
) else (
	@cd Automation
	goto skipFetchingGitRepository
)

:fetchGitRepository:
	echo Fetching git repository since it's missing
	@git clone --quiet %GIT_REMOTE_URL% Automation > nul
	@cd Automation

:skipFetchingGitRepository


python install.py %*
