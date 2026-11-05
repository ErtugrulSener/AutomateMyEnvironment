import importlib
import sys
from pathlib import Path


sys.path.insert(0, str(Path.cwd()))
modules = sorted(
    path.with_suffix("").as_posix().replace("/", ".")
    for path in Path("scripts").rglob("*.py")
    if path.name != "__init__.py"
)
failures = []
for module in modules:
    try:
        importlib.import_module(module)
    except Exception as error:
        failures.append(f"{module}: {type(error).__name__}: {error}")

print(f"Imported {len(modules) - len(failures)} of {len(modules)} modules")
for failure in failures:
    print(failure)
raise SystemExit(bool(failures))
