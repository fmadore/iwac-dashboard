#!/usr/bin/env python3
"""
IWAC Language Facets Data Generator

Fetches data from multiple subsets of the dataset:
  https://huggingface.co/datasets/fmadore/islam-west-africa-collection

Generates JSON files for pie chart facets under static/data:

1) language-global.json        -> global language distribution for pie chart
2) language-countries.json     -> language distribution by country facets
3) language-types.json         -> language distribution by type facets
4) language-metadata.json      -> metadata about the language facets

The script processes these subsets:
- articles
- audiovisual
- documents
- publications
- references

And creates faceted data for:
- Language distribution (for pie charts)
- Country filtering
- Type filtering (corresponding to subsets)
"""

from __future__ import annotations

import re
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

# Import shared utilities
from iwac_utils import (
    DATASET_ID,
    normalize_country,
    extract_year,
    find_column,
    save_json,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SUBSETS = ["articles", "audiovisual", "documents", "publications", "references"]


def _normalize_languages(value: Any) -> List[str]:
    """Split and normalize language values to a list of consistent names.

    Handles lists and strings with common delimiters like | ; , / and
    maps common codes or localized names to English names. Duplicates
    are removed while preserving order.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ["Unknown"]

    # Base mapping for common codes and localized names
    lang_mapping = {
        "fr": "French",
        "en": "English",
        "ar": "Arabic",
        "es": "Spanish",
        "de": "German",
        "pt": "Portuguese",
        "it": "Italian",
        "français": "French",
        "anglais": "English",
        "arabe": "Arabic",
        "espagnol": "Spanish",
        "allemand": "German",
        "portugais": "Portuguese",
        "italien": "Italian",
    }

    tokens: List[str] = []

    if isinstance(value, (list, tuple, set)):
        for v in value:
            if v is None or (isinstance(v, float) and pd.isna(v)):
                continue
            tokens.append(str(v))
    else:
        s = str(value).strip()
        if not s:
            return ["Unknown"]
        # Split on common separators (| ; , /)
        tokens = [t for t in re.split(r"[|;,/]", s) if t is not None]

    normalized: List[str] = []
    for t in tokens:
        name = str(t).strip()
        if not name:
            continue
        mapped = lang_mapping.get(name.lower(), name.title())
        normalized.append(mapped)

    # Deduplicate while preserving order
    deduped = list(dict.fromkeys(normalized))
    return deduped if deduped else ["Unknown"]


def load_subset_data(subset: str) -> pd.DataFrame:
    """Load data from a specific subset."""
    logger.info(f"Loading subset '{subset}'...")
    try:
        dset = load_dataset(DATASET_ID, subset)
        df = dset["train"].to_pandas()
        logger.info(f"Loaded {len(df)} rows from '{subset}' with columns: {list(df.columns)}")
        return df
    except Exception as e:
        logger.warning(f"Failed to load subset '{subset}': {e}")
        return pd.DataFrame()


def process_subset_data(df: pd.DataFrame, subset_name: str) -> List[Dict[str, Any]]:
    """Process a single subset and extract normalized data."""
    if df.empty:
        return []

    # Find relevant columns using shared utility
    language_col = find_column(df, ["language", "Language", "langue", "Langue", "lang"])
    country_col = find_column(df, ["country", "Country", "countries", "Countries", "pays", "Pays"])
    date_col = find_column(df, ["date", "Date", "created", "published", "year", "Year", "année"])
    title_col = find_column(df, ["title", "Title", "titre", "Titre", "dcterms:title"])

    records = []

    for _, row in df.iterrows():
        # Extract and normalize data
        languages = _normalize_languages(row.get(language_col) if language_col else None)
        countries = normalize_country(row.get(country_col) if country_col else None)
        year = extract_year(row.get(date_col) if date_col else None)
        title = str(row.get(title_col, "")).strip() if title_col else ""

        # Create a record for each country × language combination
        for country in countries:
            for language in languages:
                records.append({
                    "language": language,
                    "country": country,
                    "type": subset_name,
                    "year": year,
                    "title": title[:100] if title else "",
                })

    logger.info(f"Processed {len(records)} records from '{subset_name}'")
    return records


def generate_global_distribution(all_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate global language distribution for pie chart."""
    language_counts = Counter(record["language"] for record in all_records)
    
    total = sum(language_counts.values())
    
    # Convert to pie chart format
    pie_data = []
    for language, count in language_counts.most_common():
        percentage = (count / total * 100) if total > 0 else 0
        pie_data.append({
            "label": language,
            "value": count,
            "percentage": round(percentage, 1)
        })
    
    return {
        "data": pie_data,
        "total": total,
        "languages": len(language_counts),
        "generated_at": datetime.now().isoformat()
    }


def generate_country_facets(all_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate language distribution by country for faceted filtering."""
    country_language_counts = defaultdict(lambda: defaultdict(int))
    
    for record in all_records:
        country_language_counts[record["country"]][record["language"]] += 1
    
    facets = {}
    
    for country, language_counts in country_language_counts.items():
        total = sum(language_counts.values())
        
        pie_data = []
        for language, count in sorted(language_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            pie_data.append({
                "label": language,
                "value": count,
                "percentage": round(percentage, 1)
            })
        
        facets[country] = {
            "data": pie_data,
            "total": total,
            "languages": len(language_counts)
        }
    
    return {
        "facets": facets,
        "countries": sorted(facets.keys()),
        "generated_at": datetime.now().isoformat()
    }


def generate_type_facets(all_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate language distribution by type (subset) for faceted filtering."""
    type_language_counts = defaultdict(lambda: defaultdict(int))
    
    for record in all_records:
        type_language_counts[record["type"]][record["language"]] += 1
    
    facets = {}
    
    for doc_type, language_counts in type_language_counts.items():
        total = sum(language_counts.values())
        
        pie_data = []
        for language, count in sorted(language_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            pie_data.append({
                "label": language,
                "value": count,
                "percentage": round(percentage, 1)
            })
        
        facets[doc_type] = {
            "data": pie_data,
            "total": total,
            "languages": len(language_counts)
        }
    
    return {
        "facets": facets,
        "types": sorted(facets.keys()),
        "generated_at": datetime.now().isoformat()
    }


def generate_temporal_facets(all_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate language distribution over time periods."""
    # Filter records with valid years
    records_with_years = [r for r in all_records if r["year"] is not None]
    
    if not records_with_years:
        return {
            "facets": {},
            "periods": [],
            "generated_at": datetime.now().isoformat()
        }
    
    # Group by decades
    decade_language_counts = defaultdict(lambda: defaultdict(int))
    
    for record in records_with_years:
        decade = (record["year"] // 10) * 10  # Round down to nearest decade
        decade_language_counts[decade][record["language"]] += 1
    
    facets = {}
    
    for decade, language_counts in decade_language_counts.items():
        total = sum(language_counts.values())
        
        pie_data = []
        for language, count in sorted(language_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total * 100) if total > 0 else 0
            pie_data.append({
                "label": language,
                "value": count,
                "percentage": round(percentage, 1)
            })
        
        decade_label = f"{decade}s"
        facets[decade_label] = {
            "data": pie_data,
            "total": total,
            "languages": len(language_counts),
            "decade": decade
        }
    
    return {
        "facets": facets,
        "periods": sorted(facets.keys()),
        "generated_at": datetime.now().isoformat()
    }


def generate_metadata(all_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate metadata about the dataset and facets."""
    languages = set(record["language"] for record in all_records)
    countries = set(record["country"] for record in all_records)
    types = set(record["type"] for record in all_records)
    years = [record["year"] for record in all_records if record["year"] is not None]
    
    metadata = {
        "total_records": len(all_records),
        "languages": {
            "count": len(languages),
            "values": sorted(languages)
        },
        "countries": {
            "count": len(countries),
            "values": sorted(countries)
        },
        "types": {
            "count": len(types),
            "values": sorted(types)
        },
        "temporal": {
            "min_year": min(years) if years else None,
            "max_year": max(years) if years else None,
            "records_with_dates": len(years),
            "coverage_percentage": round(len(years) / len(all_records) * 100, 1) if all_records else 0
        },
        "subsets_processed": SUBSETS,
        "generated_at": datetime.now().isoformat()
    }
    
    return metadata


## save_json is imported from iwac_utils


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate language facet JSONs from IWAC subsets")
    parser.add_argument(
        "--output-dir",
        default="static/data",
        help="Directory to write JSON files (default: static/data)"
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
        logger.error("No data loaded from any subset!")
        return
    
    logger.info(f"Total records processed: {len(all_records)}")
    
    # Generate faceted data
    logger.info("Generating global language distribution...")
    global_data = generate_global_distribution(all_records)
    save_json(global_data, output_dir / "language-global.json")
    
    logger.info("Generating country facets...")
    country_data = generate_country_facets(all_records)
    save_json(country_data, output_dir / "language-countries.json")
    
    logger.info("Generating type facets...")
    type_data = generate_type_facets(all_records)
    save_json(type_data, output_dir / "language-types.json")
    
    logger.info("Generating metadata...")
    metadata = generate_metadata(all_records)
    save_json(metadata, output_dir / "language-metadata.json")
    
    logger.info("✅ Language facets data generation completed successfully!")
    logger.info(f"Generated files in {output_dir}:")
    logger.info("  - language-global.json (global distribution)")
    logger.info("  - language-countries.json (country facets)")
    logger.info("  - language-types.json (type facets)")  
    logger.info("  - language-metadata.json (metadata)")


if __name__ == "__main__":
    main()