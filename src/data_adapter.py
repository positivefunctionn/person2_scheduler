"""Handoff validation and non-overlapping horizon construction."""
import csv
REQUIRED = ("actual_cpu", "predicted_cpu", "p_overload", "actual_overload", "predicted_overload")

def load_and_validate(path, expected_rows=1084):
    with open(path, newline="", encoding="utf-8") as f: rows = list(csv.DictReader(f))
    missing = set(REQUIRED) - set(rows[0] if rows else [])
    errors = []
    if missing: errors.append("missing columns: " + ", ".join(sorted(missing)))
    if expected_rows is not None and len(rows) != expected_rows: errors.append(f"row count {len(rows)} != {expected_rows}")
    for i, r in enumerate(rows, start=2):
        try:
            p = float(r["p_overload"]); label = int(float(r["predicted_overload"])); float(r["predicted_cpu"])
            if not 0 <= p <= 1: errors.append(f"row {i}: p_overload outside [0,1]")
            if label not in (0, 1): errors.append(f"row {i}: predicted_overload not binary")
        except (ValueError, KeyError): errors.append(f"row {i}: invalid numeric field")
    return rows, {"row_count": len(rows), "errors": errors, "valid": not errors}

def horizons(rows, length):
    if length < 1: raise ValueError("horizon length must be positive")
    return [rows[i:i+length] for i in range(0, len(rows), length)]
