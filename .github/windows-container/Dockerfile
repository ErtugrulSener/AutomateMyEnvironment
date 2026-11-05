# escape=`
FROM python:3.14-windowsservercore-ltsc2025
USER ContainerAdministrator
SHELL ["powershell", "-NoLogo", "-NoProfile", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]
ENV SCOOP=C:\Software\scoop SCOOP_GLOBAL=C:\Software

RUN Invoke-WebRequest -UseBasicParsing -Uri https://github.com/git-for-windows/git/releases/download/v2.56.0.windows.4/MinGit-2.56.0.4-64-bit.zip -OutFile C:\mingit.zip; Expand-Archive -LiteralPath C:\mingit.zip -DestinationPath C:\Git; Remove-Item -LiteralPath C:\mingit.zip
RUN $env:Path = 'C:\Git\cmd;' + $env:Path; & ([scriptblock]::Create((Invoke-RestMethod https://get.scoop.sh))) -RunAsAdmin -ScoopDir $env:SCOOP -ScoopGlobalDir $env:SCOOP_GLOBAL; if (!(Test-Path -LiteralPath "$env:SCOOP\shims\scoop.cmd")) { throw 'Scoop was not installed' }

WORKDIR C:/Automation
COPY source/ C:/Automation/
COPY ci/ C:/ci/
RUN $env:Path = 'C:\Git\cmd;' + $env:Path; python -m pip install --disable-pip-version-check -r requirements-test.txt; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

CMD ["powershell", "-NoLogo", "-NoProfile", "-Command", "$env:Path = 'C:\\Git\\cmd;C:\\Software\\scoop\\shims;' + $env:Path; python -u install.py; exit $LASTEXITCODE"]
