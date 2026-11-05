$ErrorActionPreference = 'Stop'
$env:Path = 'C:\Git\cmd;C:\Software\scoop\shims;' + $env:Path
Set-Location -LiteralPath C:\Automation

git config --global --add safe.directory C:/Automation
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# main.bat expects this remote. Detached HEAD keeps its git pull from replacing the tested source.
git init --quiet
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git add .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git -c user.name=ContainerTest -c user.email=container@example.invalid commit --quiet -m 'Container test source'
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git checkout --quiet --detach
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git remote add origin https://github.com/ErtugrulSener/AutomateMyEnvironment.git
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

cmd /d /c main.bat
$installerExitCode = $LASTEXITCODE
if ($installerExitCode -ne 5) {
    throw "Expected Server Core's Defender preflight to exit 5, got $installerExitCode"
}
if (!(Select-String -LiteralPath install.log -SimpleMatch 'The tamper protection feature of Windows Defender needs to be disabled!' -Quiet)) {
    throw 'The installer did not reach the expected Defender preflight'
}
Write-Host 'Bootstrap reached the Defender preflight. The desktop configuration has not run.'

& C:\Software\apps\python314\current\python.exe -B C:\ci\check_imports.py
exit $LASTEXITCODE
