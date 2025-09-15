#!/usr/bin/env python3
"""
IWAC Index Entities Data Generator

Fetches the 'index' subset from the dataset
  https://huggingface.co/datasets/fmadore/islam-west-africa-collection
and produces two JSON files under static/data:

1) index-types.json        -> counts by Type (bar chart source)
2) index-entities.json     -> flat list of entity rows for table

Notes
- For the bar chart, entries with Type == "Notices d'autorité" are excluded.
- The script is resilient to minor column name variations (e.g. 'Titre' vs 'dcterms:title').
- Dates are normalized to YYYY-MM-DD when possible.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from datetime import datetime

try:
    from datasets import load_dataset
    import pandas as pd
except ImportError:
    print("Required packages not installed. Please run:")
    print("pip install -r scripts/requirements.txt")
    raise


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


DATASET_ID = "fmadore/islam-west-africa-collection"
INDEX_SUBSET = "index"
EXCLUDED_TYPE_FOR_BARCHART = "Notices d'autorité"  # Do not collect for bar chart


def _first_existing(df: "pd.DataFrame", candidates: Iterable[str]) -> Optional[str]:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _to_date_str(value: Any) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    # If already string, try to parse/normalize to date
    try:
        if isinstance(value, str):
            if not value:
                return None
            dt = pd.to_datetime(value, errors="coerce")
            if pd.isna(dt):
                return None
            return dt.date().isoformat()
        # Pandas/NumPy datetimes or python datetime
        if isinstance(value, (pd.Timestamp, datetime)):
            return value.date().isoformat()
        # Try generic parsing
        dt = pd.to_datetime(value, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.date().isoformat()
    except Exception:
        return None


def _normalize_countries(value: Any) -> str:
    if value is None:
        return ""
    # If it's already a list/iterable of strings
    if isinstance(value, (list, tuple, set)):
        parts = [str(x).strip() for x in value if str(x).strip()]
        return " | ".join(sorted(set(parts), key=lambda s: s.lower()))
    # If it's a string with potential separators
    s = str(value).strip()
    if not s:
        return ""
    # Normalize common separators to pipe
    for sep in [";", ",", "|"]:
        if sep in s:
            items = [p.strip() for p in s.split(sep) if p.strip()]
            return " | ".join(sorted(set(items), key=lambda x: x.lower()))
    return s


def load_index_dataframe() -> "pd.DataFrame":
    logger.info(f"Loading dataset {DATASET_ID} subset '{INDEX_SUBSET}' ...")
    dset = load_dataset(DATASET_ID, INDEX_SUBSET)
    df: pd.DataFrame = dset["train"].to_pandas()
    logger.info(f"Loaded {len(df)} index rows with columns: {list(df.columns)}")
    return df


def build_bar_chart_json(df: "pd.DataFrame") -> Dict[str, Any]:
    # Detect the Type column
    type_col = _first_existing(df, [
        "Type",
        "type",
        "Type d’entité",
        "Type d'entité",
        "entity_type",
    ])
    if not type_col:
        raise RuntimeError("Could not find a Type column in the index subset.")

    # Exclude authority records for bar chart
    filtered = df[df[type_col] != EXCLUDED_TYPE_FOR_BARCHART].copy()
    counts = filtered[type_col].value_counts().sort_values(ascending=False)

    result = {
        "labels": counts.index.tolist(),
        "values": counts.values.tolist(),
        "total": int(counts.sum()),
    }
    return result


def extract_entities_rows(df: "pd.DataFrame", include_authority: bool = True) -> List[Dict[str, Any]]:
    # Resolve key column names
    id_col = _first_existing(df, ["o:id", "o_id", "id", "ID"]) or "o:id"
    title_col = _first_existing(df, ["Titre", "dcterms:title", "title", "Title"]) or "Titre"
    type_col = _first_existing(df, [
        "Type",
        "type",
        "Type d’entité",
        "Type d'entité",
        "entity_type",
    ]) or "Type"
    freq_col = _first_existing(df, ["frequency", "occurrence_count", "occurrences", "freq"])  # optional
    first_col = _first_existing(df, [
        "first_occurrence",
        "firstOccurrence",
        "premiere_occurrence",
        "première_occurrence",
        "first_date",
    ])
    last_col = _first_existing(df, [
        "last_occurrence",
        "lastOccurrence",
        "derniere_occurrence",
        "dernière_occurrence",
        "last_date",
    ])
    countries_col = _first_existing(df, ["countries", "country", "pays", "Countries"])  # optional

    rows: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        r_type = r.get(type_col, None)
        if not include_authority and r_type == EXCLUDED_TYPE_FOR_BARCHART:
            continue

        oid = r.get(id_col, None)
        # Ensure integer if possible
        try:
            if pd.isna(oid):
                oid = None
            else:
                oid = int(oid)
        except Exception:
            # keep as-is
            pass

        frequency_val: Optional[int] = None
        if freq_col and freq_col in df.columns:
            val = r.get(freq_col, None)
            try:
                if pd.isna(val):
                    frequency_val = None
                else:
                    frequency_val = int(val)
            except Exception:
                # try length if list-like
                if isinstance(val, (list, tuple, set)):
                    frequency_val = len(val)
                else:
                    frequency_val = None

        first_val = _to_date_str(r.get(first_col)) if first_col else None
        last_val = _to_date_str(r.get(last_col)) if last_col else None
        countries_val = _normalize_countries(r.get(countries_col)) if countries_col else ""

        rows.append({
            "o:id": oid,
            "Titre": r.get(title_col, None),
            "Type": r_type,
            "frequency": frequency_val if frequency_val is not None else 0,
            "first_occurrence": first_val,
            "last_occurrence": last_val,
            "countries": countries_val,
        })

    return rows


def save_json(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    try:
        abs_path = path.resolve()
        cwd = Path.cwd().resolve()
        display = abs_path.relative_to(cwd)
    except Exception:
        display = path
    logger.info(f"Wrote {display}")


def process(output_dir: Path, include_authority_in_table: bool) -> Tuple[Path, Path]:
    df = load_index_dataframe()

    # 1) Bar chart data by Type (excluding authority records)
    bar_json = build_bar_chart_json(df)
    bar_path = output_dir / "index-types.json"
    save_json(bar_json, bar_path)

    # 2) Flat entities index for table
    rows = extract_entities_rows(df, include_authority=include_authority_in_table)
    table_path = output_dir / "index-entities.json"
    save_json(rows, table_path)

    return bar_path, table_path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate JSONs from IWAC 'index' subset")
    parser.add_argument(
        "--output-dir",
        default="static/data",
        help="Directory to write JSON files (default: static/data)",
    )
    parser.add_argument(
        "--exclude-authority-in-table",
        action="store_true",
        help="Exclude 'Notices d'autorité' from the entities table JSON (default: include)",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    include_authority = not bool(args.exclude_authority_in_table)

    if include_authority:
        logger.info("Authority records will be included in the table JSON (default).")
    else:
        logger.info("Authority records will be excluded from the table JSON.")

    try:
        bar_path, table_path = process(out_dir, include_authority)
        logger.info("✅ Index entities data generation completed successfully!")
        logger.info(f"Bar chart JSON: {bar_path}")
        logger.info(f"Table JSON:     {table_path}")
    except Exception as e:
        logger.error(f"❌ Generation failed: {e}")
        raise


if __name__ == "__main__":
    main()
