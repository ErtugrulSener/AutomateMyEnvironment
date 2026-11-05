import subprocess
from pathlib import Path

import pytest


@pytest.mark.parametrize(("ping_exit", "portqry_exit", "expected_exit"), [
    (0, 1, 0),
    (1, 0, 0),
    (1, 1, 6),
    (1, 2, 6),
])
def test_bootstrap_network_uses_fallback_result(tmp_path, ping_exit, portqry_exit, expected_exit):
    source = (Path(__file__).resolve().parents[1] / "main.bat").read_text()
    network_check = source.split(":: Check for internet connection with Ping and PortQry\n", 1)[1]
    network_check = network_check.split(":: Check for scoop installation on system", 1)[0]
    network_check = network_check.replace(
        "@Ping www.google.de -n 1 -w 1000 >NUL 2>&1", f"@cmd /d /c exit {ping_exit}"
    ).replace(
        '@"external/executables/portqry/PortQry.exe" -n google.de -p TCP -e 80 -q',
        f"@cmd /d /c exit {portqry_exit}",
    )
    probe = tmp_path / "network.cmd"
    probe.write_text(
        "@echo off\n@setlocal enabledelayedexpansion\n" + network_check
        + "echo NETWORK_PREFLIGHT_PASSED\nexit /b 0\n:end\nexit /b 0\n",
        encoding="ascii",
    )

    result = subprocess.run(["cmd", "/d", "/c", str(probe)], cwd=tmp_path, capture_output=True, text=True)

    assert result.returncode == expected_exit, result.stdout + result.stderr
    assert ("NETWORK_PREFLIGHT_PASSED" in result.stdout) is (expected_exit == 0)
    assert ("You need an active internet connection" in result.stdout) is (expected_exit == 6)
