import sys
import time
from pathlib import Path


Path("C:/Automation/logs", sys.argv[1] + ".ready").write_text("ready", encoding="ascii")
while True:
    time.sleep(1)
