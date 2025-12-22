#!/usr/bin/env python3
r"""
Unified preprocessing pipeline for IWAC Spatial Overview.

This script orchestrates the full data preparation flow:
  1) Export dataset subsets to JSON (articles.json, index.json)
  2) Enrich index.json locations with Country via world_countries.geojson
  3) Build entity files (entities/*.json) with precomputed relationships

Key features:
  - Structured logging to console and optional file
  - Step timers and result summaries
  - Flexible CLI to run specific steps and control I/O paths

Usage (PowerShell):
  # Activate venv (optional) and install deps from scripts/requirements.txt
  # python -m venv .venv
    # .\.venv\Scripts\Activate.ps1
  # pip install -r scripts/requirements.txt

  # Run all steps with defaults
  # python scripts/preprocess_all.py

  # Run specific steps
  # python scripts/preprocess_all.py --steps fetch add-countries entities

  # Customize output dir and log file
  # python scripts/preprocess_all.py --out-dir "omeka-map-explorer/static/data" --log-file "scripts/logs/preprocess.log"
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import time
from contextlib import contextmanager
from datetime import datetime
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

# Optional imports; some steps only need these lazily
try:
    from datasets import Dataset, DatasetDict, load_dataset  # type: ignore
except Exception:  # pragma: no cover - optional, validated at runtime
    Dataset = object  # type: ignore
    DatasetDict = dict  # type: ignore
    load_dataset = None  # type: ignore

try:
    from shapely.geometry import Point, shape  # type: ignore
    from shapely.prepared import prep  # type: ignore
    _HAS_SHAPELY = True
except Exception:
    _HAS_SHAPELY = False


# -------------------------
# Logging & timing utilities
# -------------------------

@contextmanager
def step_timer(name: str) -> Iterator[float]:
    start = time.perf_counter()
    logging.info(f"▶️  Start: %s", name)
    try:
        yield start
    finally:
        dur = time.perf_counter() - start
        logging.info(f"✅ Done: %s (%.2fs)", name, dur)


def setup_logging(level: str = "INFO", log_file: Optional[Path] = None) -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)
    handlers: List[logging.Handler] = [
        logging.StreamHandler()
    ]
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        handlers.append(fh)

    logging.basicConfig(
        level=lvl,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )


def _dump_json(path: Path, data: Any, compact: bool = False) -> None:
    """Write JSON to disk, optionally compact (no whitespace) for smaller files."""
    if compact:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    else:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# -------------------------
# Paths & CLI
# -------------------------

DATASET_ID_DEFAULT = "fmadore/islam-west-africa-collection"


def default_paths(script_path: Path) -> Dict[str, Path]:
    root = script_path.parent.parent.resolve()
    data_dir = root / "omeka-map-explorer" / "static" / "data"
    maps_dir = data_dir / "maps"
    entities_dir = data_dir / "entities"
    return {
        "root": root,
        "data_dir": data_dir,
        "maps_dir": maps_dir,
        "entities_dir": entities_dir,
        "world_geojson": maps_dir / "world_countries.geojson",
        "articles_json": data_dir / "articles.json",
        "index_json": data_dir / "index.json",
    }


# -------------------------
# Step 1: Dataset export
# -------------------------

def _pick_first_split(ds_dict: DatasetDict):  # type: ignore[override]
    if isinstance(ds_dict, dict):
        if "train" in ds_dict:
            return ds_dict["train"]
        first_key = next(iter(ds_dict.keys()))
        return ds_dict[first_key]
    # Best-effort for DatasetDict-like
    return ds_dict  # type: ignore[return-value]


def load_subset(dataset_id: str, subset_name: str):
    if load_dataset is None:
        raise RuntimeError("datasets is not installed. Please install: pip install datasets")

    # Try config style first
    try:
        ds_dict = load_dataset(dataset_id, subset_name)  # type: ignore[misc]
        if isinstance(ds_dict, (dict, DatasetDict)):
            return _pick_first_split(ds_dict)
        return ds_dict
    except Exception:
        pass

    # Then try split style
    return load_dataset(dataset_id, split=subset_name)  # type: ignore[misc]


def to_pipe_separated(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        parts = []
        for v in value:
            if v is None:
                continue
            if isinstance(v, (dict, list, tuple, set)):
                parts.append(json.dumps(v, ensure_ascii=False))
            else:
                parts.append(str(v))
        return " | ".join(p for p in parts if p)
    if isinstance(value, dict):
        if all(not isinstance(v, (dict, list, tuple, set)) for v in value.values()):
            return " | ".join(str(v) for v in value.values() if v is not None)
        return json.dumps(value, ensure_ascii=False)
    return str(value)


_ISO_YMD = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_ISO_YM = re.compile(r"^(\d{4})-(\d{2})$")
_ISO_Y = re.compile(r"^(\d{4})$")
_DMY_SLASH = re.compile(r"^(\d{1,2})\/(\d{1,2})\/(\d{4})$")


def normalize_date_ymd(value: Any) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if not s:
        return ""

    m = _ISO_YMD.match(s)
    if m:
        return s
    m = _ISO_YM.match(s)
    if m:
        y, mth = m.groups()
        return f"{y}-{mth}-01"
    m = _ISO_Y.match(s)
    if m:
        (y,) = m.groups()
        return f"{y}-01-01"
    m = _DMY_SLASH.match(s)
    if m:
        d, mth, y = m.groups()
        return f"{int(y):04d}-{int(mth):02d}-{int(d):02d}"
    return s


def get_first_non_empty(row: Dict[str, Any], keys: Iterable[str]) -> Any:
    for k in keys:
        if k in row:
            v = row[k]
            if v is None:
                continue
            if isinstance(v, (list, tuple, set, dict)) and not v:
                continue
            return v
    return None


def transform_articles_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "o:id": str(get_first_non_empty(row, ["o:id", "o_id", "id"])) or "",
        "title": str(get_first_non_empty(row, ["title", "dcterms:title", "Titre"])) or "",
        "newspaper": str(get_first_non_empty(row, ["newspaper", "dcterms:publisher", "publisher"])) or "",
        "country": str(get_first_non_empty(row, ["country", "pays", "Country"])) or "",
        "pub_date": normalize_date_ymd(get_first_non_empty(row, ["pub_date", "date", "dcterms:date"])) or "",
        "subject": to_pipe_separated(get_first_non_empty(row, ["subject", "dcterms:subject"])) or "",
        "spatial": to_pipe_separated(get_first_non_empty(row, ["spatial", "dcterms:spatial"])) or "",
    }


def transform_index_row(row: Dict[str, Any]) -> Dict[str, Any]:
    oid = get_first_non_empty(row, ["o:id", "o_id", "id"])  # keep numeric if possible
    try:
        oid_num: Optional[int] = int(oid) if oid is not None and str(oid).strip() else None
    except Exception:
        oid_num = None

    return {
        "o:id": oid_num if oid_num is not None else None,
        "Titre": str(get_first_non_empty(row, ["Titre", "title", "dcterms:title"])) or "",
        "Type": str(get_first_non_empty(row, ["Type", "type"])) or "",
        "Coordonnées": str(
            get_first_non_empty(row, ["Coordonnées", "coordinates", "coordonnees", "curation:coordinates"])
        )
        or "",
    }


@dataclass
class FetchResult:
    articles_count: int
    index_count: int
    articles_path: Path
    index_path: Path


def step_fetch(dataset_id: str, out_dir: Path, *, compact: bool = False) -> FetchResult:
    out_dir.mkdir(parents=True, exist_ok=True)

    with step_timer("Export dataset subsets to JSON"):
        articles_ds = load_subset(dataset_id, "articles")
        index_ds = load_subset(dataset_id, "index")

        # Transform rows (ensure iteration works for Dataset/DatasetDict or plain lists)
        articles_rows = [transform_articles_row(r) for r in articles_ds]  # type: ignore[arg-type]
        index_rows = [transform_index_row(r) for r in index_ds]  # type: ignore[arg-type]

        articles_path = out_dir / "articles.json"
        index_path = out_dir / "index.json"
        _dump_json(articles_path, articles_rows, compact)
        _dump_json(index_path, index_rows, compact)

        logging.info("Wrote %d articles -> %s", len(articles_rows), articles_path)
        logging.info("Wrote %d index entries -> %s", len(index_rows), index_path)

        return FetchResult(
            articles_count=len(articles_rows),
            index_count=len(index_rows),
            articles_path=articles_path,
            index_path=index_path,
        )


# -------------------------
# Step 2: Add Countries
# -------------------------

def parse_coordinates(coord_str: str) -> Optional[Tuple[float, float]]:
    if not coord_str or not coord_str.strip():
        return None
    try:
        cleaned = (
            coord_str.replace("(", "").replace(")", "").replace("[", "").replace("]", "").strip()
        )
        parts = [p.strip() for p in cleaned.split(",")]
        if len(parts) >= 2:
            lat = float(parts[0])
            lng = float(parts[1])
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return (lat, lng)
        return None
    except (ValueError, IndexError):
        return None


def load_world_countries(geojson_path: Path) -> List[Dict[str, Any]]:
    with geojson_path.open("r", encoding="utf-8") as f:
        world_data = json.load(f)
    countries: List[Dict[str, Any]] = []
    for feature in world_data.get("features", []):
        props = feature.get("properties", {})
        name = props.get("name")
        geom = feature.get("geometry")
        if not name or not geom:
            continue
        try:
            shp = shape(geom)
            countries.append({
                "name": name,
                "geometry": prep(shp),  # prepared for fast contains
                "properties": props,
            })
        except Exception as e:
            logging.warning("Failed to prepare geometry for %s: %s", name, e)
    logging.info("Loaded %d countries from %s", len(countries), geojson_path)
    return countries


def find_country_for_coordinates(lat: float, lng: float, countries: List[Dict[str, Any]]) -> Optional[str]:
    pt = Point(lng, lat)
    for c in countries:
        try:
            if c["geometry"].contains(pt):
                return c["name"]
        except Exception:
            # ignore and continue
            continue
    return None


@dataclass
class CountryResult:
    processed: int
    matched: int
    skipped_non_locations: int
    updated_index_path: Path


def _load_named_polygons(geojson_path: Path, name_keys: List[str]) -> List[Dict[str, Any]]:
    """Load polygons with a name extracted from properties using the first matching key.

    Returns a list of dicts: {"name": str, "geometry": prepared geometry, "properties": props}
    """
    with geojson_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    items: List[Dict[str, Any]] = []
    for feature in data.get("features", []):
        props = feature.get("properties", {}) or {}
        raw_name: Optional[str] = None
        for k in name_keys:
            if k in props and props[k]:
                raw_name = str(props[k])
                break
        geom = feature.get("geometry")
        if not raw_name or not geom:
            continue
        try:
            shp = shape(geom)
            items.append({
                "name": raw_name,
                "geometry": prep(shp),
                "properties": props,
            })
        except Exception as e:
            logging.warning("Failed to prepare geometry for %s in %s: %s", raw_name, geojson_path.name, e)
    logging.info("Loaded %d features from %s", len(items), geojson_path)
    return items


def _find_name_for_point(lat: float, lng: float, features: List[Dict[str, Any]]) -> Optional[str]:
    pt = Point(lng, lat)
    for f in features:
        try:
            # intersects includes boundary; more robust than contains for points on borders
            if f["geometry"].intersects(pt):
                return f["name"]
        except Exception:
            continue
    return None


def step_add_countries(index_path: Path, world_geojson: Path, maps_dir: Optional[Path] = None, *, compact: bool = False) -> CountryResult:
    if not _HAS_SHAPELY:
        raise RuntimeError("shapely is required for add-countries step. Install with: pip install shapely")
    if not world_geojson.exists():
        raise FileNotFoundError(f"world_countries.geojson not found at {world_geojson}")

    with step_timer("Add Country/Region/Prefecture to locations in index.json"):
        countries = load_world_countries(world_geojson)
        with index_path.open("r", encoding="utf-8") as f:
            index_rows: List[Dict[str, Any]] = json.load(f)

    # Note: backup creation removed to keep output directory minimal and avoid extra files

        # Preload administrative layers if maps_dir is provided
        admin_layers: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
        if maps_dir is None:
            # Try to infer maps_dir from index_path (../maps relative to data dir)
            potential = index_path.parent / "maps"
            if potential.exists():
                maps_dir = potential
        if maps_dir is not None:
            try:
                admin_layers = {
                    "Benin": {
                        "region": _load_named_polygons(maps_dir / "benin_regions.geojson", ["name", "NAME", "NAME_1"]),
                        "prefecture": _load_named_polygons(maps_dir / "benin_prefectures.geojson", ["name", "NAME", "NAME_2"]),
                    },
                    "Burkina Faso": {
                        "region": _load_named_polygons(maps_dir / "burkina_faso_regions.geojson", ["name", "NAME", "NAME_1"]),
                        "prefecture": _load_named_polygons(maps_dir / "burkina_faso_prefectures.geojson", ["name", "NAME", "NAME_2"]),
                    },
                    "Togo": {
                        "region": _load_named_polygons(maps_dir / "togo_regions.geojson", ["name", "NAME", "NAME_1"]),
                        # togo prefectures store prefecture in shape2
                        "prefecture": _load_named_polygons(maps_dir / "togo_prefectures.geojson", ["shape2", "name", "NAME_2"]),
                    },
                    "Côte d'Ivoire": {
                        # Cote d'Ivoire regions file uses shape2 for the region label
                        "region": _load_named_polygons(maps_dir / "cote_divoire_regions.geojson", ["shape2", "name", "NAME", "NAME_1"]),
                    },
                }
            except FileNotFoundError as e:
                logging.warning("Some admin layer files are missing: %s", e)

        processed = matched = skipped = 0
        TARGET_COUNTRIES = {"Benin", "Burkina Faso", "Togo", "Côte d'Ivoire"}
        for row in index_rows:
            if row.get("Type") != "Lieux":
                skipped += 1
                continue
            coord_str = row.get("Coordonnées", "") or ""
            coords = parse_coordinates(coord_str)
            if coords:
                lat, lng = coords
                country = find_country_for_coordinates(lat, lng, countries)
                row["Country"] = country or ""
                if country:
                    matched += 1
                    # Enrich with Region/Prefecture only for target countries
                    if country in TARGET_COUNTRIES:
                        layers = admin_layers.get(country)
                        if layers:
                            try:
                                region_val = None
                                pref_val = None
                                if "region" in layers:
                                    region_val = _find_name_for_point(lat, lng, layers["region"])
                                if "prefecture" in layers:
                                    pref_val = _find_name_for_point(lat, lng, layers["prefecture"])
                                if region_val:
                                    row["Region"] = region_val
                                else:
                                    row.pop("Region", None)
                                if pref_val:
                                    row["Prefecture"] = pref_val
                                else:
                                    row.pop("Prefecture", None)
                            except Exception as e:
                                logging.debug("Admin match failed for %s at (%s,%s): %s", country, lat, lng, e)
                    else:
                        # Ensure we don't carry empty fields for non-target countries
                        row.pop("Region", None)
                        row.pop("Prefecture", None)
            else:
                row["Country"] = ""
                # Remove admin fields if no coordinates
                row.pop("Region", None)
                row.pop("Prefecture", None)
            processed += 1

        _dump_json(index_path, index_rows, compact)

        logging.info("Processed %d locations, matched %d countries, skipped %d non-locations", processed, matched, skipped)
    return CountryResult(processed=processed, matched=matched, skipped_non_locations=skipped, updated_index_path=index_path)


# -------------------------
# Step 3: Entities
# -------------------------

def parse_pipe_list(s: str) -> List[str]:
    if not s:
        return []
    return [item.strip() for item in s.split("|") if item.strip()]


def step_entities(data_dir: Path, entities_dir: Path, *, compact: bool = False) -> Dict[str, int]:
    with step_timer("Build entity files from articles/index"):
        articles_path = data_dir / "articles.json"
        index_path = data_dir / "index.json"
        with articles_path.open("r", encoding="utf-8") as fa:
            articles: List[Dict[str, Any]] = json.load(fa)
        with index_path.open("r", encoding="utf-8") as fi:
            index_data: List[Dict[str, Any]] = json.load(fi)

        # Build entity -> article IDs map (from article spatial and subject fields)
        entity_articles: Dict[str, set[str]] = {}
        for a in articles:
            aid = str(a.get("o:id", ""))
            # Add spatial entities (locations)
            for spatial in parse_pipe_list(a.get("spatial", "")):
                entity_articles.setdefault(spatial, set()).add(aid)
            # Add subject entities (persons, organizations, events, subjects)
            for subj in parse_pipe_list(a.get("subject", "")):
                entity_articles.setdefault(subj, set()).add(aid)

        # Types mapping
        type_to_file = {
            "Personnes": "persons",
            "Organisations": "organizations",
            "Événements": "events",
            "Sujets": "subjects",
            "Lieux": "locations",
        }

        entities_by_file: Dict[str, List[Dict[str, Any]]] = {v: [] for v in type_to_file.values()}

        for entry in index_data:
            etype = entry.get("Type", "")
            if etype not in type_to_file:
                continue
            name = entry.get("Titre", "")
            eid = str(entry.get("o:id", ""))
            related = sorted(entity_articles.get(name, set()))
            if not related:
                continue

            record: Dict[str, Any] = {
                "id": eid,
                "name": name,
                "relatedArticleIds": related,
                "articleCount": len(related),
            }
            if etype == "Lieux":
                coordinates_str = (entry.get("Coordonnées", "") or "").strip()
                country = (entry.get("Country", "") or "").strip()
                region = (entry.get("Region", "") or "").strip()
                prefecture = (entry.get("Prefecture", "") or "").strip()
                coords: Optional[List[float]] = None
                pc = parse_coordinates(coordinates_str)
                if pc is not None:
                    coords = [pc[0], pc[1]]
                # Only add non-empty fields to reduce file size
                loc_extra: Dict[str, Any] = {"coordinatesRaw": coordinates_str}
                if coords is not None:
                    loc_extra["coordinates"] = coords
                if country:
                    loc_extra["country"] = country
                if region:
                    loc_extra["region"] = region
                if prefecture:
                    loc_extra["prefecture"] = prefecture
                record.update(loc_extra)

            entities_by_file[type_to_file[etype]].append(record)

        # Sort entities by name for stable output
        for items in entities_by_file.values():
            items.sort(key=lambda x: x["name"])  # type: ignore[no-any-return]

        # Write files
        entities_dir.mkdir(parents=True, exist_ok=True)
        counts: Dict[str, int] = {}
        for fname, entities in entities_by_file.items():
            out_path = entities_dir / f"{fname}.json"
            _dump_json(out_path, entities, compact)
            counts[fname] = len(entities)
            logging.info("Saved %d %s -> %s", len(entities), fname, out_path)

        return counts


# -------------------------
# CLI & main
# -------------------------

def parse_args() -> argparse.Namespace:
    script_path = Path(__file__).resolve()
    paths = default_paths(script_path)

    p = argparse.ArgumentParser(description="Unified preprocessing pipeline for IWAC Spatial Overview")
    p.add_argument("--dataset-id", default=DATASET_ID_DEFAULT, help="Hugging Face dataset ID")
    p.add_argument("--out-dir", default=str(paths["data_dir"]), help="Output directory for articles.json and index.json")
    p.add_argument("--world-geojson", default=str(paths["world_geojson"]), help="Path to world_countries.geojson")
    p.add_argument("--entities-dir", default=str(paths["entities_dir"]), help="Output directory for entities/*.json")
    p.add_argument("--maps-dir", default=str(paths["maps_dir"]), help="Directory containing administrative GeoJSON files")
    p.add_argument("--compact", action="store_true", help="Write compact (minified) JSON to reduce file size")
    p.add_argument(
        "--steps",
        nargs="*",
        choices=["fetch", "add-countries", "entities"],
        help="Limit to specific steps (default: run all in order)",
    )
    p.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    p.add_argument("--log-file", default=None, help="Optional log file path")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    log_file = Path(args.log_file) if args.log_file else None
    setup_logging(args.log_level, log_file)

    data_dir = Path(args.out_dir).resolve()
    world_geojson = Path(args.world_geojson).resolve()
    entities_dir = Path(args.entities_dir).resolve()
    maps_dir = Path(args.maps_dir).resolve() if getattr(args, "maps_dir", None) else None

    selected_steps = args.steps or ["fetch", "add-countries", "entities"]

    script_path = Path(__file__).resolve()
    paths = default_paths(script_path)

    totals: Dict[str, Any] = {}

    logging.info("Preprocess pipeline starting | steps=%s", ",".join(selected_steps))

    if "fetch" in selected_steps:
        res = step_fetch(args.dataset_id, data_dir, compact=args.compact)
        totals["articles"] = res.articles_count
        totals["index"] = res.index_count

    if "add-countries" in selected_steps:
        index_path = data_dir / "index.json"
        if not index_path.exists():
            raise FileNotFoundError(f"index.json not found at {index_path}; run 'fetch' step first or provide correct --out-dir")
        res2 = step_add_countries(index_path, world_geojson, maps_dir, compact=args.compact)
        totals["locationsProcessed"] = res2.processed
        totals["countriesMatched"] = res2.matched
        totals["nonLocationsSkipped"] = res2.skipped_non_locations

    if "entities" in selected_steps:
        counts = step_entities(data_dir, entities_dir, compact=args.compact)
        totals.update({f"entities_{k}": v for k, v in counts.items()})

    logging.info("All steps complete: %s", json.dumps(totals, ensure_ascii=False))


if __name__ == "__main__":
    main()
