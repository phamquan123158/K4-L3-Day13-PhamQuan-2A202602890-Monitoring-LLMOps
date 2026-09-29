from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

from scripts import dashboard


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_validator(config_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "validate_dashboard.py"),
            "--config",
            str(config_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_repository_dashboard_contract_is_valid() -> None:
    result = run_validator(REPO_ROOT / "config" / "dashboard.yaml")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "6/6 panel" in result.stdout


def test_dashboard_loads_only_recent_valid_jsonl_records(
    monkeypatch, tmp_path: Path
) -> None:
    current_time = datetime.now(timezone.utc)
    current_record = {
        "ts": current_time.isoformat(),
        "event": "response_sent",
        "latency_ms": 120,
    }
    old_record = {
        "ts": (current_time - timedelta(minutes=61)).isoformat(),
        "event": "response_sent",
        "latency_ms": 9000,
    }
    log_path = tmp_path / "logs.jsonl"
    log_path.write_text(
        json.dumps(current_record) + "\nnot-json\n" + json.dumps(old_record) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(dashboard, "LOG_PATH", log_path)

    records = dashboard.load_records()

    assert len(records) == 1
    assert records[0]["event"] == "response_sent"
    assert records[0]["latency_ms"] == 120


def test_validator_rejects_panel_without_threshold(tmp_path: Path) -> None:
    payload = yaml.safe_load(
        (REPO_ROOT / "config" / "dashboard.yaml").read_text(encoding="utf-8")
    )
    del payload["dashboard"]["panels"][0]["threshold"]
    invalid_config = tmp_path / "dashboard.yaml"
    invalid_config.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    result = run_validator(invalid_config)

    assert result.returncode == 1
    assert "latency.threshold" in result.stdout


def test_validator_rejects_panel_without_query_example(tmp_path: Path) -> None:
    payload = yaml.safe_load(
        (REPO_ROOT / "config" / "dashboard.yaml").read_text(encoding="utf-8")
    )
    payload["dashboard"]["panels"][0].pop("query", None)
    invalid_config = tmp_path / "dashboard.yaml"
    invalid_config.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )

    result = run_validator(invalid_config)

    assert result.returncode == 1
    assert "latency.query" in result.stdout
