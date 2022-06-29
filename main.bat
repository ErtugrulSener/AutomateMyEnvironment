@echo off
@cls

:: Variables
set GIT_REMOTE_URL=https://github.com/ErtugrulSener/Automation.git


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
@SET remote_url_in_folder=
FOR /F "tokens=*" %%a in ('git config --get remote.origin.url') do SET remote_url_in_folder=%%a

if "%remote_url_in_folder%"=="%GIT_REMOTE_URL%" (
	goto skipFetchingGitRepository
) else (
	goto fetchGitRepository
)

:fetchGitRepository:
	echo Fetching git repository since it's missing
	@git clone --quiet %GIT_REMOTE_URL% Automation > nul
	@cd Automation

:skipFetchingGitRepository



:: Check if requirements for python script are installed
@python -c "import pkg_resources; pkg_resources.require(open('requirements.txt',mode='r'))" 2> nul

if %ERRORLEVEL% NEQ 0 (
	goto installPythonDependencies
) else (
	goto skipInstallingPythonDependencies
)

:installPythonDependencies:
	echo Installing python dependencies since they're missing
	@pip install --ignore-installed -r requirements.txt
	@cls

:skipInstallingPythonDependencies


python install.py %*
