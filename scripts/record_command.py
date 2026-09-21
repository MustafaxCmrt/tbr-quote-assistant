"""Run an argv command and retain its actual output/exit code in reports/."""

import datetime
from pathlib import Path
import shlex
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
report = root / "reports" / sys.argv[1]
command = sys.argv[2:]
result = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
body = (
    f"UTC: {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n"
    f"Base commit (working tree may contain pending changes): {sha}\n"
    f"Command: {shlex.join(command)}\nExit code: {result.returncode}\n\n{result.stdout}"
)
report.parent.mkdir(exist_ok=True)
report.write_text(body)
print(body)
sys.exit(result.returncode)
