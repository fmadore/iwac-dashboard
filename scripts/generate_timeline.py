#!/usr/bin/env python3
"""
IWAC Collection Growth Timeline Data Generator

Fetches data from multiple subsets of the dataset:
  https://huggingface.co/datasets/fmadore/islam-west-africa-collection

Generates JSON files for timeline visualization under static/data:

1) timeline-growth.json          -> monthly additions and cumulative total
2) timeline-types.json           -> monthly growth faceted by document type
3) timeline-countries.json       -> monthly growth faceted by country
4) timeline-metadata.json        -> metadata about the timeline data

The script processes these subsets:
- articles        -> Press Article / Article de presse
- publications    -> Islamic Periodical / Périodique islamique
- documents       -> Document
- audiovisual     -> Audiovisuel
- references      -> Reference / Référence

And tracks collection growth over time using the 'added_date' field.
"""

from __future__ import annotations
import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
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
    extract_month,
    find_column,
    save_json,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SUBSETS = ["articles", "audiovisual", "documents", "publications", "references"]

# Mapping from subset names to document type labels (English / French)
SUBSET_TO_TYPE = {
    "articles": {"en": "Press Article", "fr": "Article de presse"},
    "publications": {"en": "Islamic Periodical", "fr": "Périodique islamique"},
    "documents": {"en": "Document", "fr": "Document"},
    "audiovisual": {"en": "Audiovisuel", "fr": "Audiovisuel"},
    "references": {"en": "Reference", "fr": "Référence"},
}


def load_subset_data(subset: str) -> pd.DataFrame:
    """Load data from a specific subset."""
    logger.info(f"Loading subset '{subset}'...")
    try:
        dset = load_dataset(DATASET_ID, subset)
        df = dset["train"].to_pandas()
        logger.info(f"Loaded {len(df)} records from '{subset}'")
        return df
    except Exception as e:
        logger.error(f"Error loading subset '{subset}': {e}")
        return pd.DataFrame()


def process_subset_data(df: pd.DataFrame, subset_name: str) -> List[Dict[str, Any]]:
    """Process a single subset and extract normalized data with added_date, type, and country."""
    if df.empty:
        return []

    # Find relevant columns using shared utility
    country_col = find_column(df, ["country", "Country", "countries", "Countries", "pays", "Pays"])
    added_date_col = find_column(df, ["added_date", "addedDate", "added", "created_at", "createdAt"])

    if not added_date_col:
        logger.warning(f"No 'added_date' column found in subset '{subset_name}'")
        return []

    # Get document type labels
    type_labels = SUBSET_TO_TYPE.get(subset_name, {"en": subset_name.title(), "fr": subset_name.title()})

    records = []

    for _, row in df.iterrows():
        month = extract_month(row.get(added_date_col))

        if not month:
            continue

        countries = normalize_country(row.get(country_col) if country_col else None)

        for country in countries:
            records.append({
                "month": month,
                "subset": subset_name,
                "type_en": type_labels["en"],
                "type_fr": type_labels["fr"],
                "country": country,
            })

    logger.info(f"Processed {len(records)} records with added_date from '{subset_name}'")
    return records


def generate_global_timeline(all_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate global timeline with monthly additions and cumulative total."""
    logger.info("Generating global timeline data...")
    
    # Count additions per month
    month_counts = Counter(record["month"] for record in all_records)
    
    # Sort months chronologically
    sorted_months = sorted(month_counts.keys())
    
    # Calculate monthly additions and cumulative total
    monthly_additions = []
    cumulative_total = []
    running_total = 0
    
    for month in sorted_months:
        count = month_counts[month]
        running_total += count
        
        monthly_additions.append(count)
        cumulative_total.append(running_total)
    
    result = {
        "months": sorted_months,
        "monthly_additions": monthly_additions,
        "cumulative_total": cumulative_total,
        "total_records": len(all_records),
        "month_range": {
            "min": sorted_months[0] if sorted_months else None,
            "max": sorted_months[-1] if sorted_months else None
        },
        "generated_at": datetime.now().isoformat()
    }
    
    logger.info(f"Generated global timeline with {len(sorted_months)} months")
    return result


def generate_type_faceted_timeline(all_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate timeline data faceted by document type."""
    logger.info("Generating type-faceted timeline data...")
    
    # Group by type and month
    type_month_counts = defaultdict(lambda: defaultdict(int))
    
    for record in all_records:
        type_key = record["type_en"]
        month = record["month"]
        type_month_counts[type_key][month] += 1
    
    # Get all unique months across all types
    all_months = sorted(set(
        month
        for type_data in type_month_counts.values()
        for month in type_data.keys()
    ))
    
    # Build faceted data for each type
    facets = {}
    
    for type_en, month_data in type_month_counts.items():
        # Get the French label (find the first record with this type)
        type_fr = next(
            (r["type_fr"] for r in all_records if r["type_en"] == type_en),
            type_en
        )
        
        # Build monthly series with cumulative total
        monthly_additions = []
        cumulative_total = []
        running_total = 0
        
        for month in all_months:
            count = month_data.get(month, 0)
            running_total += count
            
            monthly_additions.append(count)
            cumulative_total.append(running_total)
        
        facets[type_en] = {
            "label_en": type_en,
            "label_fr": type_fr,
            "months": all_months,
            "monthly_additions": monthly_additions,
            "cumulative_total": cumulative_total,
            "total_records": sum(month_data.values()),
            "month_range": {
                "min": all_months[0] if all_months else None,
                "max": all_months[-1] if all_months else None
            }
        }
    
    result = {
        "facets": facets,
        "types": sorted(facets.keys()),
        "generated_at": datetime.now().isoformat()
    }
    
    logger.info(f"Generated type-faceted timeline for {len(facets)} types")
    return result


def generate_country_faceted_timeline(all_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate timeline data faceted by country."""
    logger.info("Generating country-faceted timeline data...")
    
    # Group by country and month
    country_month_counts = defaultdict(lambda: defaultdict(int))
    
    for record in all_records:
        country = record["country"]
        month = record["month"]
        country_month_counts[country][month] += 1
    
    # Get all unique months across all countries
    all_months = sorted(set(
        month
        for country_data in country_month_counts.values()
        for month in country_data.keys()
    ))
    
    # Build faceted data for each country
    facets = {}
    
    for country, month_data in country_month_counts.items():
        # Build monthly series with cumulative total
        monthly_additions = []
        cumulative_total = []
        running_total = 0
        
        for month in all_months:
            count = month_data.get(month, 0)
            running_total += count
            
            monthly_additions.append(count)
            cumulative_total.append(running_total)
        
        facets[country] = {
            "months": all_months,
            "monthly_additions": monthly_additions,
            "cumulative_total": cumulative_total,
            "total_records": sum(month_data.values()),
            "month_range": {
                "min": all_months[0] if all_months else None,
                "max": all_months[-1] if all_months else None
            }
        }
    
    result = {
        "facets": facets,
        "countries": sorted(facets.keys()),
        "generated_at": datetime.now().isoformat()
    }
    
    logger.info(f"Generated country-faceted timeline for {len(facets)} countries")
    return result


def generate_metadata(all_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate metadata about the timeline dataset."""
    months = [record["month"] for record in all_records]
    countries = set(record["country"] for record in all_records)
    types_en = set(record["type_en"] for record in all_records)
    
    # Count records per subset
    subset_counts = Counter(record["subset"] for record in all_records)
    
    return {
        "total_records": len(all_records),
        "unique_months": len(set(months)),
        "month_range": {
            "min": min(months) if months else None,
            "max": max(months) if months else None
        },
        "countries": sorted(countries),
        "country_count": len(countries),
        "types": sorted(types_en),
        "type_count": len(types_en),
        "subset_counts": dict(subset_counts),
        "subsets_processed": SUBSETS,
        "generated_at": datetime.now().isoformat()
    }


## save_json is imported from iwac_utils


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate timeline data from IWAC dataset")
    parser.add_argument(
        "--output-dir",
        default="static/data",
        help="Directory to write JSON files (default: static/data)",
    )
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    
    logger.info("=" * 60)
    logger.info("IWAC Collection Growth Timeline Data Generator")
    logger.info("=" * 60)
    
    try:
        # Load and process all subsets
        all_records = []
        
        for subset in SUBSETS:
            df = load_subset_data(subset)
            if not df.empty:
                records = process_subset_data(df, subset)
                all_records.extend(records)
        
        if not all_records:
            logger.error("No records with added_date found in any subset")
            return
        
        logger.info(f"Total records with added_date: {len(all_records)}")
        
        # Generate all output files
        logger.info("\nGenerating output files...")
        
        # 1. Global timeline
        global_data = generate_global_timeline(all_records)
        save_json(global_data, output_dir / "timeline-growth.json")
        
        # 2. Type-faceted timeline
        type_data = generate_type_faceted_timeline(all_records)
        save_json(type_data, output_dir / "timeline-types.json")
        
        # 3. Country-faceted timeline
        country_data = generate_country_faceted_timeline(all_records)
        save_json(country_data, output_dir / "timeline-countries.json")
        
        # 4. Metadata
        metadata = generate_metadata(all_records)
        save_json(metadata, output_dir / "timeline-metadata.json")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Timeline data generation completed successfully!")
        logger.info("=" * 60)
        
        # Copy to build directory if it exists
        build_dir = Path("build/data")
        if build_dir.exists():
            logger.info("\nCopying files to build/data...")
            for file in ["timeline-growth.json", "timeline-types.json", 
                        "timeline-countries.json", "timeline-metadata.json"]:
                src = output_dir / file
                dst = build_dir / file
                if src.exists():
                    dst.write_bytes(src.read_bytes())
                    logger.info(f"Copied {file} to build/data")
        
    except Exception as e:
        logger.error(f"❌ Timeline data generation failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
