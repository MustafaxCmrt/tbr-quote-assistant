"""Real HTTP checks. Start the API with DEBUG_STREAM_SMOKE=1 before running."""

import json
import subprocess
import time
from urllib.error import HTTPError
from urllib.request import urlopen


base = "http://127.0.0.1:8000"
with urlopen(f"{base}/health/live", timeout=5) as response:
    assert response.status == 200
    assert json.load(response) == {"status": "ok"}
print("PASS GET /health/live: 200, status=ok")
try:
    urlopen(f"{base}/api/debug/stream-smoke", timeout=5)
    raise AssertionError("GET must not open a POST-only stream")
except HTTPError as error:
    assert error.code == 405
print("PASS debug endpoint is POST-only")

command = ["curl", "-N", "--silent", "--show-error", "--fail", "--max-time", "10",
           "-X", "POST", "-H", "Accept: text/event-stream", f"{base}/api/debug/stream-smoke"]
print("Command:", " ".join(command), flush=True)
started = time.monotonic()
process = subprocess.Popen(command, stdout=subprocess.PIPE, text=True, encoding="utf-8")
events = []
data = []
arrival = []
assert process.stdout is not None
for line in process.stdout:
    elapsed = time.monotonic() - started
    print(f"{elapsed:.3f}s {line.rstrip()}", flush=True)
    if line.startswith("event: "):
        events.append(line.removeprefix("event: ").strip())
        arrival.append(elapsed)
    if line.startswith("data: "):
        data.append(json.loads(line.removeprefix("data: ")))
assert process.wait() == 0
assert events == ["text_delta", "text_delta", "done"], events
assert data == [
    {"debug": True, "event_seq": 1, "text": "Bağlantı çalışıyor ğüşiöç"},
    {"debug": True, "event_seq": 2, "text": "İkinci parça ulaştı: ĞÜŞİÖÇ"},
    {"debug": True, "event_seq": 3},
], data
assert all(0.8 <= later - earlier <= 3 for earlier, later in zip(arrival, arrival[1:])), arrival
print("PASS two UTF-8 events and done arrived incrementally, gaps:",
      [round(later - earlier, 3) for earlier, later in zip(arrival, arrival[1:])])
