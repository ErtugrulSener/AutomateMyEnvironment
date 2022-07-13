@echo off
@cls

:: Variables
set GIT_REMOTE_URL=https://github.com/ErtugrulSener/AutomateMyEnvironment.git

set SCOOP=C:\Software\scoop
set SCOOP_GLOBAL=C:\Software

set scoop_path=%SCOOP_GLOBAL%\scoop\shims
set refreshenv_path=%SCOOP_GLOBAL%\apps\refreshenv\current

set PATH=%PATH%;%scoop_path%;%refreshenv_path%



:: Check for scoop installation on system
@call scoop >NUL 2>&1

if %ERRORLEVEL% NEQ 0 (
	goto installScoop
) else (
	goto skipScoopInstallation
)

:installScoop
	echo Setting global environments parameters
	@setx SCOOP "%SCOOP%" /M
	@setx SCOOP_GLOBAL "%SCOOP_GLOBAL%" /M

	echo Installing scoop windows package manager
	@powershell Set-ExecutionPolicy Unrestricted
	@powershell iex """& {$(irm get.scoop.sh)} -RunAsAdmin"""

	

:skipScoopInstallation



:: Check for refreshenv installation on system
@call refreshenv >NUL 2>&1

if %ERRORLEVEL% NEQ 0 (
	goto installRefreshenv
) else (
	goto skipRefreshenvInstallation
)

:installRefreshenv
	echo Installing refreshenv
	@call scoop install -g refreshenv >NUL 2>&1
	@call refreshenv >NUL 2>&1

:skipRefreshenvInstallation



:: Check for git installation on system
@call git --version >NUL 2>&1

if %ERRORLEVEL% NEQ 0 (
	goto installGitViaScoop
) else (
	goto skipGitInstallation
)

:installGitViaScoop
	echo Installing git
	@call scoop install -g git >NUL 2>&1
	@call refreshenv >NUL 2>&1

:skipGitInstallation



:: Check for git-crypt installation on system
@call git-crypt --version >NUL 2>&1

if %ERRORLEVEL% NEQ 0 (
	goto installGitCryptViaScoop
) else (
	goto skipGitCryptInstallation
)

:installGitCryptViaScoop
	echo Installing git-crypt
	@call scoop install -g git-crypt >NUL 2>&1
	@call refreshenv >NUL 2>&1

:skipGitCryptInstallation


@call scoop bucket add extras >NUL 2>&1
@call scoop bucket add java >NUL 2>&1
@call scoop bucket add versions >NUL 2>&1



:: Check for python 3 installation on system
@call python --version 3 >NUL 2>&1

if %ERRORLEVEL% NEQ 0 (
	goto installPythonViaScoop
) else (
	goto skipPythonInstallation
)

:installPythonViaScoop:
	echo Installing python
	@call scoop install -g python >NUL 2>&1
	@call refreshenv >NUL 2>&1

	echo Updating pip to the newest version
	@call python -m pip install --upgrade pip >NUL 2>&1

:skipPythonInstallation



:: Check if Automation folder exits already
if exist Automation\ (
	@cd Automation
	goto skipFetchingGitRepository
) else (
	goto skipCheckingForAutomationFolder
)

:skipCheckingForAutomationFolder

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
	@git clone --quiet %GIT_REMOTE_URL% Automation >NUL 2>&1
	@cd Automation

:skipFetchingGitRepository



:: Check if requirements for python script are installed
@call python -c "import pkg_resources; pkg_resources.require(open('requirements.txt',mode='r'))" >NUL 2>&1

if %ERRORLEVEL% NEQ 0 (
	goto installPythonDependencies
) else (
	goto skipInstallingPythonDependencies
)

:installPythonDependencies:
	echo Installing python dependencies
	@pip install --ignore-installed -r requirements.txt

:skipInstallingPythonDependencies


REM @cls
git pull --quiet >NUL 2>&1
python install.py %*
