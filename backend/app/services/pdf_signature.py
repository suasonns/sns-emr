import hashlib
import json


def compute_document_hash(chart: dict) -> str:
    """
    Create a deterministic SHA-256 hash of the chart data.
    Any modification to chart content changes the hash.
    """
    normalized = json.dumps(chart, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()