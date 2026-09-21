"""Evidence accompanies existing assertions; setup/call/teardown outcomes are never inferred."""

import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        scenario = getattr(item, "callspec", None)
        if scenario is None or "scenario" not in scenario.params:
            continue
        scenario = scenario.params["scenario"]
        item.golden_evidence = {
            "scenario_id": scenario["scenario_id"],
            "status": "not_run",
            "expected_tools": scenario["expected_tool_calls"],
            "expected_sources": scenario["expected_sources"],
            "user_message": scenario["user_message"],
            "actual_tools": [],
            "source_ids": [],
            "before": None,
            "after": None,
            "error": None,
            "phases": {},
            "run_timestamp": datetime.now(UTC).isoformat(),
            "commit_sha": os.environ.get("EVIDENCE_COMMIT_SHA", "unknown"),
        }


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    result = yield
    report = result.get_result()
    evidence = getattr(item, "golden_evidence", None)
    if evidence is None:
        return
    evidence["phases"][report.when] = {"outcome": report.outcome, "seconds": report.duration}
    if report.failed:
        evidence["status"] = "failed" if report.when == "call" else "error"
        evidence["error"] = report.longreprtext
    elif report.skipped and evidence["status"] not in {"failed", "error"}:
        evidence["status"] = "skipped"
    elif report.when == "teardown" and all(
        evidence["phases"].get(phase, {}).get("outcome") == "passed"
        for phase in ("setup", "call", "teardown")
    ):
        evidence["status"] = "passed"


def encode(value):
    if isinstance(value, (Decimal, datetime)):
        return str(value)
    raise TypeError(f"Unsupported evidence type: {type(value).__name__}")


def pytest_sessionfinish(session, exitstatus):
    output = os.environ.get("GOLDEN_REPORT_PATH")
    if not output:
        return
    records = [item.golden_evidence for item in session.items if hasattr(item, "golden_evidence")]
    body = {
        "exit_code": int(exitstatus),
        "transport": "HTTP routes via httpx ASGITransport; live SSE timing is separate evidence",
        "counts": {
            status: sum(r["status"] == status for r in records)
            for status in ("passed", "failed", "error", "skipped", "not_run")
        },
        "scenarios": records,
    }
    Path(output).write_text(json.dumps(body, ensure_ascii=False, indent=2, default=encode) + "\n")
