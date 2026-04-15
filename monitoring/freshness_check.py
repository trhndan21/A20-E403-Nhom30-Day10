
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml  # Thêm để read contract

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_contract_sla(contract_path: Path) -> Tuple[float, str]:
    """
    Load SLA hours và alert channel từ data_contract.yaml.
    """
    if not contract_path.is_file():
        logger.warning(f"Contract file missing: {contract_path}")
        return 24.0, "group-report-and-runbook"  # Default

    with contract_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    freshness = data.get("freshness", {})
    sla_hours = freshness.get("sla_hours", 24.0)
    alert_channel = freshness.get("alert_channel", "group-report-and-runbook")
    return sla_hours, alert_channel


def get_watermark_db() -> datetime:
    """
    Giả lập đọc watermark từ DB (ví dụ: max effective_date từ raw data).
    Trong thực tế, query DB.
    """
    # Giả lập: đọc từ raw CSV max effective_date
    raw_path = Path(__file__).parent.parent / "data" / "raw" / "policy_export_dirty.csv"
    if not raw_path.is_file():
        return datetime.now(timezone.utc) - timezone.timedelta(hours=48)  # Giả lập stale

    import csv
    max_dt = None
    with raw_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_iso(row.get("effective_date", ""))
            if dt and (max_dt is None or dt > max_dt):
                max_dt = dt
    return max_dt or datetime.now(timezone.utc)


def parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        # Cho phép "2026-04-10T08:00:00" không có timezone
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def check_manifest_freshness(
    manifest_path: Path,
    *,
    sla_hours: float = 24.0,
    now: datetime | None = None,
    contract_path: Path | None = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Trả về ("PASS" | "WARN" | "FAIL", detail dict).

    Đọc trường `latest_exported_at` hoặc max exported_at trong cleaned summary.
    Mở rộng: so sánh với watermark DB, batch clock.
    """
    now = now or datetime.now(timezone.utc)
    if contract_path:
        sla_hours, alert_channel = load_contract_sla(contract_path)
    else:
        alert_channel = "group-report-and-runbook"

    if not manifest_path.is_file():
        return "FAIL", {"reason": "manifest_missing", "path": str(manifest_path), "alert_channel": alert_channel}

    data: Dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    ts_raw = data.get("latest_exported_at") or data.get("run_timestamp")
    dt = parse_iso(str(ts_raw)) if ts_raw else None
    if dt is None:
        return "WARN", {"reason": "no_timestamp_in_manifest", "manifest": data, "alert_channel": alert_channel}

    age_hours = (now - dt).total_seconds() / 3600.0
    watermark_dt = get_watermark_db()
    watermark_age = (now - watermark_dt).total_seconds() / 3600.0
    batch_clock_diff = (dt - watermark_dt).total_seconds() / 3600.0 if watermark_dt else None

    detail = {
        "latest_exported_at": ts_raw,
        "age_hours": round(age_hours, 3),
        "sla_hours": sla_hours,
        "watermark_age_hours": round(watermark_age, 3),
        "batch_clock_diff_hours": round(batch_clock_diff, 3) if batch_clock_diff else None,
        "alert_channel": alert_channel,
    }
    if age_hours <= sla_hours:
        return "PASS", detail
    return "FAIL", {**detail, "reason": "freshness_sla_exceeded"}


def alert_freshness(status: str, detail: Dict[str, Any]) -> None:
    """
    Alert dựa trên status và detail.
    """
    channel = detail.get("alert_channel", "group-report-and-runbook")
    if status == "FAIL":
        logger.error(f"Freshness FAIL: {detail} -> Notify {channel}")
        # Trong thực tế: send email/slack to channel
    elif status == "WARN":
        logger.warning(f"Freshness WARN: {detail} -> Notify {channel}")


def check_batch_freshness(
    manifests_dir: Path,
    contract_path: Path | None = None,
    now: datetime | None = None,
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Check freshness cho tất cả manifests trong dir.
    """
    results = []
    for manifest in manifests_dir.glob("*.json"):
        status, detail = check_manifest_freshness(manifest, now=now, contract_path=contract_path)
        alert_freshness(status, detail)
        results.append((status, detail))
    return results
