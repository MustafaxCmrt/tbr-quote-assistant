"""Check the running Compose stack: admin writes need the key, the web proxy adds it server-side,
the key never reaches browser-served files, and oversized bodies are rejected. Changes no data:
authorised requests use an invalid price (rejected after authentication) or rewrite the current
stock value through the web proxy.

Usage: python3 scripts/check_admin_runtime.py [--lan]
--lan also repeats the unauthenticated write against the Mac's Wi-Fi address (not printed).
"""

import json
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
env = dict(
    line.split("=", 1) for line in (root / ".env").read_text().splitlines() if "=" in line
)
key = env.get("ADMIN_API_KEY", "")
assert key, "ADMIN_API_KEY missing in .env; run python3 scripts/init_env.py"
api = "http://127.0.0.1:" + env.get("API_PORT", "8001")
web = "http://127.0.0.1:" + env.get("WEB_PORT", "5173")
invalid = {"price_try": "-1"}


def call(url, method="GET", body=None, headers=None):
    data = body if isinstance(body, bytes) else None if body is None else json.dumps(body).encode()
    request = Request(
        url, data=data, method=method, headers={"Content-Type": "application/json", **(headers or {})}
    )
    try:
        with urlopen(request, timeout=10) as response:
            return response.status, response.read().decode()
    except HTTPError as error:
        return error.code, error.read().decode()


def code(text):
    try:
        return json.loads(text).get("error", {}).get("code")
    except ValueError:
        return None


product = api + "/api/products/PRD-BC-110"
before = call(product)[1]
checks = [
    ("API write without key", call(product, "PATCH", invalid), 401, "ADMIN_KEY_REQUIRED"),
    (
        "API write with wrong key",
        call(product, "PATCH", invalid, {"X-Admin-Key": "wrong"}),
        401,
        "ADMIN_KEY_REQUIRED",
    ),
    ("Web proxy write adds key (validation 422, no write)", call(web + "/api/products/PRD-BC-110", "PATCH", invalid), 422, None),
    (
        "Web proxy valid write (same stock value)",
        call(web + "/api/products/PRD-BC-110", "PATCH", {"stock_qty": json.loads(before)["stock_qty"]}),
        200,
        None,
    ),
    ("Web proxy read", call(web + "/api/products?limit=1"), 200, None),
    ("API read without key", call(api + "/api/products?limit=1"), 200, None),
    (
        "API body over 256 KiB",
        call(api + "/api/chat", "POST", b'{"message":"' + b"x" * 300_000 + b'"}'),
        413,
        "PAYLOAD_TOO_LARGE",
    ),
]
if "--lan" in sys.argv:
    lan = subprocess.run(["ipconfig", "getifaddr", "en0"], capture_output=True, text=True).stdout.strip()
    assert lan, "No Wi-Fi address on en0"
    lan_api = f"http://{lan}:" + env.get("API_PORT", "8001")
    checks += [
        ("LAN (address redacted) readiness", call(lan_api + "/health/ready"), 200, None),
        ("LAN (address redacted) write without key", call(lan_api + "/api/products/PRD-BC-110", "PATCH", invalid), 401, "ADMIN_KEY_REQUIRED"),
    ]
for path in ["/", "/src/main.tsx", "/src/api/client.ts", "/@fs/proc/self/environ", "/@fs/app/.env"]:
    status, text = call(web + path)
    checks.append((f"Web file {path} does not contain the key (HTTP {status})", (key not in text, ""), True, None))

failed = False
for name, (status, text), expected, expected_code in checks:
    ok = status == expected and (expected_code is None or code(text) == expected_code)
    failed |= not ok
    print(("PASS " if ok else "FAIL ") + name + f": {status}" + (f" {code(text)}" if expected_code else ""))
unchanged = call(product)[1] == before
failed |= not unchanged
print(("PASS " if unchanged else "FAIL ") + "PRD-BC-110 unchanged after all requests")
sys.exit(1 if failed else 0)
