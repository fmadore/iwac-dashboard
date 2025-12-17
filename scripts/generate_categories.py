#!/usr/bin/env python3
"""
IWAC Categories Data Generator

Fetches data from multiple subsets of the dataset:
  https://huggingface.co/datasets/fmadore/islam-west-africa-collection

Generates JSON files for stacked bar chart visualization under static/data:

1) categories-global.json           -> global stacked bar chart by type over years
2) categories-{country}.json        -> per-country stacked bar chart by type over years
3) categories-metadata.json         -> metadata about the categories data

The script processes these subsets (excluding 'index'):
- articles        -> Press Article / Article de presse
- publications    -> Islamic Periodical / Périodique islamique
- documents       -> Document
- audiovisual     -> Audiovisuel
- references      -> Reference / Référence

And creates:
- Stacked bar chart data by type over years
- Country-specific faceted data
- Metadata about temporal coverage and document types
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict, Counter
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
SUBSETS = ["articles", "audiovisual", "documents", "publications", "references"]

# Mapping from subset names to document type labels (English / French)
SUBSET_TO_TYPE = {
    "articles": {"en": "Press Article", "fr": "Article de presse"},
    "publications": {"en": "Islamic Periodical", "fr": "Périodique islamique"},
    "documents": {"en": "Document", "fr": "Document"},
    "audiovisual": {"en": "Audiovisuel", "fr": "Audiovisuel"},
    "references": {"en": "Reference", "fr": "Référence"},
}


def _normalize_country(value: Any) -> List[str]:
    """Normalize country values to list of countries."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ["Unknown"]
    
    if isinstance(value, (list, tuple)):
        countries = [str(c).strip().title() for c in value if str(c).strip()]
        return countries if countries else ["Unknown"]
    
    country_str = str(value).strip()
    if not country_str:
        return ["Unknown"]
    
    # Handle multiple countries separated by common delimiters
    for sep in [";", ",", "|", "/"]:
        if sep in country_str:
            countries = [c.strip().title() for c in country_str.split(sep) if c.strip()]
            return countries if countries else ["Unknown"]
    
    return [country_str.title()]


def _extract_year(value: Any) -> Optional[int]:
    """Extract year from various date formats."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    
    try:
        # If it's already a string that looks like a year
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            # Try to extract 4-digit year
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', value)
            if year_match:
                year = int(year_match.group(0))
                if 1900 <= year <= 2100:
                    return year
        
        # Try pandas datetime parsing
        dt = pd.to_datetime(value, errors="coerce")
        if pd.notna(dt):
            year = dt.year
            if 1900 <= year <= 2100:
                return year
            
    except Exception:
        pass
    
    return None


def load_subset_data(subset: str) -> pd.DataFrame:
    """Load data from a specific subset."""
    logger.info(f"Loading subset '{subset}'...")
    try:
        dset = load_dataset(DATASET_ID, subset)
        df: pd.DataFrame = dset["train"].to_pandas()
        logger.info(f"Loaded {len(df)} records from '{subset}'")
        return df
    except Exception as e:
        logger.error(f"Failed to load subset '{subset}': {e}")
        return pd.DataFrame()


def process_subset_data(df: pd.DataFrame, subset_name: str) -> List[Dict[str, Any]]:
    """Process a single subset and extract normalized data with year and country."""
    if df.empty:
        return []
    
    # Try to find relevant columns with various naming patterns
    def find_column(candidates: List[str]) -> Optional[str]:
        for c in candidates:
            if c in df.columns:
                return c
        return None
    
    country_col = find_column(["country", "Country", "countries", "Countries", "pays", "Pays"])
    date_col = find_column(["date", "Date", "created", "published", "pub_date", "year", "Year", "année"])
    type_col = find_column(["type", "Type", "document_type", "DocumentType"])
    
    # Get document type labels (defaults)
    type_labels = SUBSET_TO_TYPE.get(subset_name, {"en": subset_name.title(), "fr": subset_name.title()})
    
    records = []
    
    for _, row in df.iterrows():
        # Extract year
        year = None
        if date_col:
            year = _extract_year(row.get(date_col))
        
        # Skip records without year (we need temporal data for the chart)
        if year is None:
            continue
        
        # Extract countries
        countries = ["Unknown"]
        if country_col:
            countries = _normalize_country(row.get(country_col))
        
        # For references subset, use actual type value if available
        if subset_name == "references" and type_col:
            actual_type = row.get(type_col)
            if actual_type and isinstance(actual_type, str) and actual_type.strip():
                actual_type = actual_type.strip()
                # Use the actual type value for both English and French
                # (assuming the type values are language-neutral or already in the data)
                type_en = actual_type
                type_fr = actual_type
            else:
                type_en = type_labels["en"]
                type_fr = type_labels["fr"]
        else:
            type_en = type_labels["en"]
            type_fr = type_labels["fr"]
        
        # Create a record for each country (for faceted data)
        for country in countries:
            records.append({
                "subset": subset_name,
                "type_en": type_en,
                "type_fr": type_fr,
                "year": year,
                "country": country,
            })
    
    logger.info(f"Processed {len(records)} records with year data from '{subset_name}'")
    return records


def generate_global_stacked_data(all_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate global stacked bar chart data by type over years."""
    logger.info("Generating global stacked bar chart data...")
    
    # Group by year and type
    year_type_counts = defaultdict(lambda: defaultdict(int))
    
    for record in all_records:
        year = record["year"]
        type_en = record["type_en"]
        year_type_counts[year][type_en] += 1
    
    # Get all years and types
    all_years = sorted(year_type_counts.keys())
    all_types = sorted(set(
        type_name 
        for year_data in year_type_counts.values() 
        for type_name in year_data.keys()
    ))
    
    # Build series data for stacked bar chart
    # Format: { "series": [{"name": "Type", "data": [count_per_year]}, ...], "years": [...] }
    series = []
    for type_name in all_types:
        type_data = [year_type_counts[year].get(type_name, 0) for year in all_years]
        series.append({
            "name": type_name,
            "data": type_data
        })
    
    result = {
        "years": all_years,
        "series": series,
        "total_records": len(all_records),
        "year_range": {
            "min": min(all_years) if all_years else None,
            "max": max(all_years) if all_years else None
        },
        "generated_at": datetime.now().isoformat()
    }
    
    logger.info(f"Generated global data with {len(all_years)} years and {len(all_types)} types")
    return result


def generate_country_stacked_data(all_records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Generate per-country stacked bar chart data by type over years."""
    logger.info("Generating country-wise stacked bar chart data...")
    
    # Group records by country
    country_records = defaultdict(list)
    for record in all_records:
        country = record["country"]
        country_records[country].append(record)
    
    country_data = {}
    
    for country, records in country_records.items():
        # Skip "Unknown" country for individual files (keep in global)
        if country == "Unknown":
            continue
        
        # Group by year and type for this country
        year_type_counts = defaultdict(lambda: defaultdict(int))
        
        for record in records:
            year = record["year"]
            type_en = record["type_en"]
            year_type_counts[year][type_en] += 1
        
        # Get all years and types for this country
        all_years = sorted(year_type_counts.keys())
        all_types = sorted(set(
            type_name 
            for year_data in year_type_counts.values() 
            for type_name in year_data.keys()
        ))
        
        # Build series data
        series = []
        for type_name in all_types:
            type_data = [year_type_counts[year].get(type_name, 0) for year in all_years]
            series.append({
                "name": type_name,
                "data": type_data
            })
        
        country_data[country] = {
            "country": country,
            "years": all_years,
            "series": series,
            "total_records": len(records),
            "year_range": {
                "min": min(all_years) if all_years else None,
                "max": max(all_years) if all_years else None
            },
            "generated_at": datetime.now().isoformat()
        }
    
    logger.info(f"Generated stacked bar chart data for {len(country_data)} countries")
    return country_data


def generate_metadata(all_records: List[Dict[str, Any]], country_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Generate metadata about the categories dataset."""
    years = [record["year"] for record in all_records]
    countries = set(record["country"] for record in all_records)
    types_en = set(record["type_en"] for record in all_records)
    
    # Count records per subset
    subset_counts = Counter(record["subset"] for record in all_records)
    
    metadata = {
        "total_records": len(all_records),
        "records_with_year": len(years),
        "coverage_percentage": 100.0,  # We only keep records with years
        "temporal": {
            "min_year": min(years) if years else None,
            "max_year": max(years) if years else None,
            "year_count": len(set(years))
        },
        "countries": {
            "count": len(countries),
            "values": sorted(countries),
            "with_individual_files": sorted([c for c in countries if c != "Unknown"])
        },
        "document_types": {
            "count": len(types_en),
            "values": sorted(types_en)
        },
        "subsets": {
            "processed": SUBSETS,
            "counts": dict(subset_counts)
        },
        "files_generated": {
            "global": "global.json",
            "countries": [f"{country.lower().replace(' ', '-')}.json" 
                         for country in sorted(country_data.keys())],
            "metadata": "metadata.json"
        },
        "type_mapping": SUBSET_TO_TYPE,
        "generated_at": datetime.now().isoformat()
    }
    
    return metadata


def save_json(data: Any, path: Path, minify: bool = True) -> None:
    """Save data as JSON file. Minified by default for faster loading."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        if minify:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    try:
        abs_path = path.resolve()
        cwd = Path.cwd().resolve()
        display = abs_path.relative_to(cwd)
    except Exception:
        display = path
    
    # Log file size for monitoring
    size_kb = path.stat().st_size / 1024
    logger.info(f"Wrote {display} ({size_kb:.1f} KB)")


def copy_to_build_dir(output_dir: Path) -> None:
    """Copy generated files to build/data/categories directory."""
    import shutil
    
    build_dir = Path("build/data/categories")
    if not build_dir.parent.exists():
        logger.info("build/data directory does not exist, skipping copy")
        return
    
    # Create build/data/categories if it doesn't exist
    build_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Copying files to build/data/categories directory...")
    for json_file in output_dir.glob("*.json"):
        dest = build_dir / json_file.name
        shutil.copy2(json_file, dest)
        logger.info(f"Copied {json_file.name} to build/data/categories/")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate category stacked bar chart JSONs from IWAC subsets")
    parser.add_argument(
        "--output-dir",
        default="static/data/categories",
        help="Directory to write JSON files (default: static/data/categories)"
    )
    parser.add_argument(
        "--subsets",
        nargs="+",
        default=SUBSETS,
        help=f"Subsets to process (default: {' '.join(SUBSETS)})"
    )
    
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    subsets_to_process = args.subsets
    
    logger.info(f"Processing subsets: {', '.join(subsets_to_process)}")
    
    # Load and process all subset data
    all_records = []
    
    for subset in subsets_to_process:
        df = load_subset_data(subset)
        records = process_subset_data(df, subset)
        all_records.extend(records)
    
    if not all_records:
        logger.error("No records with year data found. Cannot generate visualizations.")
        return
    
    logger.info(f"Total records with year data: {len(all_records)}")
    
    # Generate global stacked bar chart data
    global_data = generate_global_stacked_data(all_records)
    global_path = output_dir / "global.json"
    save_json(global_data, global_path)
    
    # Generate country-specific stacked bar chart data
    country_data = generate_country_stacked_data(all_records)
    
    for country, data in country_data.items():
        # Create filename from country name
        filename = f"{country.lower().replace(' ', '-')}.json"
        country_path = output_dir / filename
        save_json(data, country_path)
    
    # Generate metadata
    metadata = generate_metadata(all_records, country_data)
    metadata_path = output_dir / "metadata.json"
    save_json(metadata, metadata_path)
    
    # Copy to build directory
    copy_to_build_dir(output_dir)
    
    logger.info("✅ Category data generation completed successfully!")
    logger.info(f"Generated files in {output_dir}:")
    logger.info(f"  - Global: global.json")
    logger.info(f"  - Countries: {len(country_data)} individual files")
    logger.info(f"  - Metadata: metadata.json")


if __name__ == "__main__":
    main()
