from __future__ import annotations

import csv
import io
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib import request

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from app.db.session import SessionLocal
except Exception:  # pragma: no cover
    from app.core.database import SessionLocal  # type: ignore

from app.models.physician import PhysicianPecosCache

ORDER_AND_REFERRING_URL = os.getenv(
    "CMS_ORDER_AND_REFERRING_URL",
    "https://data.cms.gov/download/ltmj-23p8/application%2Fzip",
)
OPT_OUT_AFFIDAVITS_URL = os.getenv(
    "CMS_OPT_OUT_AFFIDAVITS_URL",
    "https://data.cms.gov/download/yqf2-3w3h/application%2Fzip",
)

# NOTE:
# data.cms.gov periodically rotates download artifacts. Override the URLs above
# with current dataset download URLs if CMS republishes the files under a new ID.
# The endpoint remains safe when this cache table is empty; /physicians/pecos-check
# returns {status: "unknown"} until this script successfully loads data.


def _normalize_header(value: str) -> str:
    return "".join(ch for ch in (value or "").strip().lower() if ch.isalnum())


def _normalize_npi(value: str | None) -> str | None:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits or None


def _download_bytes(url: str) -> bytes:
    with request.urlopen(url, timeout=90.0) as response:
        return response.read()


def _iter_csv_rows(payload: bytes) -> Iterable[dict[str, str]]:
    if payload[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            csv_name = next((name for name in archive.namelist() if name.lower().endswith(".csv")), None)
            if not csv_name:
                raise RuntimeError("CMS archive did not contain a CSV file")
            decoded = archive.read(csv_name).decode("utf-8-sig", errors="ignore")
    else:
        decoded = payload.decode("utf-8-sig", errors="ignore")

    reader = csv.DictReader(io.StringIO(decoded))
    for row in reader:
        yield {(_normalize_header(key)): (value or "").strip() for key, value in row.items()}


def _find_value(row: dict[str, str], *candidates: str) -> str | None:
    for candidate in candidates:
        normalized = _normalize_header(candidate)
        if normalized in row and row[normalized]:
            return row[normalized]
    return None


def _load_order_and_referring() -> dict[str, dict[str, str | None]]:
    entries: dict[str, dict[str, str | None]] = {}
    for row in _iter_csv_rows(_download_bytes(ORDER_AND_REFERRING_URL)):
        npi = _normalize_npi(_find_value(row, "npi", "npi_number"))
        if not npi:
            continue
        entries[npi] = {
            "status": "enrolled",
            "source": "CMS Order and Referring",
            "reason": _find_value(row, "primary specialty", "specialty", "provider specialty") or "Present in CMS Order and Referring dataset",
            "checked_at": None,
        }
    return entries


def _load_opt_out_affidavits() -> dict[str, dict[str, str | None]]:
    entries: dict[str, dict[str, str | None]] = {}
    for row in _iter_csv_rows(_download_bytes(OPT_OUT_AFFIDAVITS_URL)):
        npi = _normalize_npi(_find_value(row, "npi", "national provider identifier (npi)", "nationalprovideridentifiernpi"))
        if not npi:
            continue
        entries[npi] = {
            "status": "opted_out",
            "source": "CMS Opt-Out Affidavits",
            "reason": _find_value(row, "specialty", "provider specialty") or "Present in CMS Opt-Out Affidavits dataset",
            "checked_at": None,
        }
    return entries


def main() -> int:
    print("Downloading CMS Order and Referring dataset...")
    status_by_npi = _load_order_and_referring()
    print(f"Loaded {len(status_by_npi):,} enrolled NPIs")

    print("Downloading CMS Opt-Out Affidavits dataset...")
    opt_out_entries = _load_opt_out_affidavits()
    print(f"Loaded {len(opt_out_entries):,} opted-out NPIs")
    status_by_npi.update(opt_out_entries)

    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        existing = {
            entry.npi: entry
            for entry in db.query(PhysicianPecosCache).all()
        }
        created = 0
        updated = 0
        for npi, payload in status_by_npi.items():
            record = existing.get(npi)
            if record is None:
                record = PhysicianPecosCache(npi=npi)
                db.add(record)
                created += 1
            else:
                updated += 1
            record.status = str(payload["status"])
            record.source = payload["source"]
            record.reason = payload["reason"]
            record.checked_at = payload["checked_at"]
            record.refreshed_at = now
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"PECOS cache refresh complete: {created:,} created, {updated:,} updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
