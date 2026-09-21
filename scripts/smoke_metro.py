"""Check local Metro startup without placing the private LAN address in logs."""

import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen

root = Path(__file__).resolve().parents[1]
env = {**os.environ, "EXPO_NO_DOTENV": "1", "EXPO_PUBLIC_API_BASE_URL": "http://127.0.0.1:8000", "CI": "1"}
command = ["node", "node_modules/expo/bin/cli", "start", "apps/mobile", "--localhost", "--port", "8081"]
print("Command:", " ".join(command), flush=True)
with tempfile.TemporaryFile(mode="w+") as output:
    process = subprocess.Popen(command, cwd=root, env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        for attempt in range(30):
            if process.poll() is not None:
                raise RuntimeError("Metro exited before becoming ready")
            try:
                with urlopen("http://localhost:8081/status", timeout=1) as response:
                    assert response.read().decode() == "packager-status:running"
                    print("PASS Metro HTTP /status: packager-status:running")
                    break
            except URLError as error:
                if attempt == 29:
                    print("Last readiness error:", error)
                time.sleep(0.5)
        else:
            raise RuntimeError("Metro readiness timeout")
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=10)
        output.seek(0)
        print(output.read())
        print("Metro process exit after requested shutdown:", process.returncode)
print("Native device result: not_verified (localhost startup only)")
