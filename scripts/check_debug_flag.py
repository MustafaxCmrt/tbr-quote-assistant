"""Check route registration without needing DB, Docker, or third-party test tools."""

import os
from app.main import create_app

path = "/api/debug/stream-smoke"
for flag, enabled in [(None, False), ("0", False), ("false", False), ("invalid", False), ("1", True), ("true", True)]:
    if flag is None:
        os.environ.pop("DEBUG_STREAM_SMOKE", None)
    else:
        os.environ["DEBUG_STREAM_SMOKE"] = flag
    paths = create_app().openapi()["paths"]
    assert (path in paths) is enabled, flag
    assert "/health/live" in paths
    assert "/health/ready" not in paths
    print(f"PASS DEBUG_STREAM_SMOKE={flag!r}: debug route registered={enabled}")
