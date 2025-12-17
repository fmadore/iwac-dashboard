#!/usr/bin/env python3
"""
IWAC References Data Generator

Fetches data from the 'references' subset of the dataset:
  https://huggingface.co/datasets/fmadore/islam-west-africa-collection

Generates JSON files for references visualizations under static/data:

1) references-by-year-global.json       -> distribution of references by year and type (global)
2) references-by-year-{country}.json    -> distribution by year and type per country
3) references-authors.json              -> top authors by publication count
4) references-authors-{country}.json    -> top authors per country
5) references-metadata.json             -> metadata about the references data

Data extraction:
- author: multivalue field separated by |
- country: multivalue field separated by |
- pub_date: normalized to YYYY format (from yyyy-mm-dd, yyyy-mm, or yyyy)
- o:resource_class: reference type
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
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
SUBSET = "references"


def normalize_multivalue_field(value: Any, separator: str = "|") -> List[str]:
    """Normalize a multivalue field separated by a delimiter."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    
    if isinstance(value, (list, tuple)):
        items = [str(item).strip() for item in value if str(item).strip()]
        return items
    
    value_str = str(value).strip()
    if not value_str:
        return []
    
    # Split by separator and clean up
    items = [item.strip() for item in value_str.split(separator) if item.strip()]
    return items


def normalize_country(value: Any) -> List[str]:
    """Normalize country field (multivalue separated by |)."""
    countries = normalize_multivalue_field(value, "|")
    
    if not countries:
        return ["Unknown"]
    
    # Title case and deduplicate
    countries = list(dict.fromkeys([c.title() for c in countries]))
    return countries


def normalize_authors(value: Any) -> List[str]:
    """Normalize author field (multivalue separated by |)."""
    authors = normalize_multivalue_field(value, "|")
    
    if not authors:
        return []
    
    # Clean up author names and deduplicate
    cleaned_authors = []
    seen = set()
    
    for author in authors:
        # Remove extra whitespace
        author = " ".join(author.split())
        
        # Skip if empty or already seen
        if not author or author.lower() in seen:
            continue
        
        seen.add(author.lower())
        cleaned_authors.append(author)
    
    return cleaned_authors


def extract_year(value: Any) -> Optional[int]:
    """Extract year from pub_date field (yyyy-mm-dd, yyyy-mm, or yyyy)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    
    value_str = str(value).strip()
    if not value_str:
        return None
    
    # Try to extract 4-digit year (1900-2100)
    year_match = re.search(r'\b(19|20)\d{2}\b', value_str)
    if year_match:
        year = int(year_match.group(0))
        if 1900 <= year <= 2100:
            return year
    
    return None


def normalize_reference_type(value: Any) -> str:
    """Normalize reference type from o:resource_class field."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "Unknown"
    
    type_str = str(value).strip()
    if not type_str:
        return "Unknown"
    
    # Common reference type mappings
    # Keep original names but clean them up
    return type_str


def load_references_data() -> pd.DataFrame:
    """Load data from the references subset."""
    logger.info(f"Loading references subset from {DATASET_ID}...")
    try:
        dset = load_dataset(DATASET_ID, SUBSET)
        df: pd.DataFrame = dset["train"].to_pandas()
        logger.info(f"Loaded {len(df)} records from references subset")
        return df
    except Exception as e:
        logger.error(f"Failed to load references subset: {e}")
        return pd.DataFrame()


def process_references_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Process references data and extract normalized records."""
    if df.empty:
        logger.warning("Empty dataframe received")
        return []
    
    logger.info("Processing references data...")
    
    # Find relevant columns
    def find_column(candidates: List[str]) -> Optional[str]:
        for c in candidates:
            if c in df.columns:
                return c
        return None
    
    author_col = find_column(["author", "Author", "authors", "Authors"])
    country_col = find_column(["country", "Country", "countries", "Countries", "pays", "Pays"])
    date_col = find_column(["pub_date", "date", "Date", "published", "year", "Year"])
    type_col = find_column(["o:resource_class", "resource_class", "type", "Type"])
    title_col = find_column(["title", "Title", "o:title"])
    id_col = find_column(["identifier", "Identifier", "id", "ID", "o:id"])
    
    logger.info(f"Found columns: author={author_col}, country={country_col}, date={date_col}, type={type_col}, id={id_col}")
    
    records = []
    skipped_no_year = 0
    skipped_no_author = 0
    
    for idx, row in df.iterrows():
        # Get the identifier from the dataset (or fall back to index)
        pub_id = None
        if id_col:
            id_val = row.get(id_col)
            if id_val and not (isinstance(id_val, float) and pd.isna(id_val)):
                pub_id = str(id_val).strip()
        
        # Fallback to row index if no identifier
        if not pub_id:
            pub_id = f"ref_{idx}"
        
        # Extract year (required for temporal analysis)
        year = None
        if date_col:
            year = extract_year(row.get(date_col))
        
        # Extract authors (required for author analysis)
        authors = []
        if author_col:
            authors = normalize_authors(row.get(author_col))
        
        # Extract countries
        countries = ["Unknown"]
        if country_col:
            countries = normalize_country(row.get(country_col))
        
        # Extract reference type
        ref_type = "Unknown"
        if type_col:
            ref_type = normalize_reference_type(row.get(type_col))
        
        # Extract title (optional, for display)
        title = ""
        if title_col:
            title_val = row.get(title_col)
            if title_val and not (isinstance(title_val, float) and pd.isna(title_val)):
                title = str(title_val).strip()
        
        # Create records with different tracking
        # For temporal analysis: need year
        if year:
            for country in countries:
                for author in (authors if authors else [None]):
                    records.append({
                        "pub_id": pub_id,
                        "year": year,
                        "country": country,
                        "type": ref_type,
                        "author": author,
                        "title": title,
                        "has_year": True,
                        "has_author": author is not None
                    })
        else:
            skipped_no_year += 1
            # Still track for author-only stats if we have authors
            if authors:
                for country in countries:
                    for author in authors:
                        records.append({
                            "pub_id": pub_id,
                            "year": None,
                            "country": country,
                            "type": ref_type,
                            "author": author,
                            "title": title,
                            "has_year": False,
                            "has_author": True
                        })
            else:
                skipped_no_author += 1
    
    logger.info(f"Processed {len(records)} individual records")
    logger.info(f"Skipped {skipped_no_year} records without year")
    logger.info(f"Skipped {skipped_no_author} records without year or author")
    
    return records


def generate_by_year_data(records: List[Dict[str, Any]], country_filter: Optional[str] = None) -> Dict[str, Any]:
    """Generate references by year and type data."""
    # Filter records with years
    year_records = [r for r in records if r["has_year"]]
    
    # Apply country filter if specified
    if country_filter:
        year_records = [r for r in year_records if r["country"] == country_filter]
        logger.info(f"Generating by-year data for {country_filter}: {len(year_records)} records")
    else:
        logger.info(f"Generating global by-year data: {len(year_records)} records")
    
    if not year_records:
        return {
            "years": [],
            "series": [],
            "total_records": 0,
            "year_range": {"min": None, "max": None},
            "country": country_filter,
            "generated_at": datetime.now().isoformat()
        }
    
    # Group by year and type, tracking unique publications
    year_type_pub_ids = defaultdict(lambda: defaultdict(set))
    
    for record in year_records:
        year = record["year"]
        ref_type = record["type"]
        pub_id = record["pub_id"]
        
        # Track unique pub_ids per year-type combination
        year_type_pub_ids[year][ref_type].add(pub_id)
    
    # Get all years and types
    all_years = sorted(year_type_pub_ids.keys())
    all_types = sorted(set(
        type_name 
        for year_data in year_type_pub_ids.values() 
        for type_name in year_data.keys()
    ))
    
    # Build series data for stacked bar chart
    series = []
    for type_name in all_types:
        # Count unique publications per year for this type
        type_data = [len(year_type_pub_ids[year].get(type_name, set())) for year in all_years]
        series.append({
            "name": type_name,
            "data": type_data
        })
    
    # Count total unique publications across all years
    all_unique_pub_ids = set()
    for year_data in year_type_pub_ids.values():
        for pub_ids in year_data.values():
            all_unique_pub_ids.update(pub_ids)
    
    result = {
        "years": all_years,
        "series": series,
        "total_records": len(all_unique_pub_ids),  # Count unique publications
        "year_range": {
            "min": min(all_years) if all_years else None,
            "max": max(all_years) if all_years else None
        },
        "country": country_filter,
        "generated_at": datetime.now().isoformat()
    }
    
    return result


def generate_authors_data(records: List[Dict[str, Any]], country_filter: Optional[str] = None) -> Dict[str, Any]:
    """Generate top authors by publication count."""
    # Filter records with authors
    author_records = [r for r in records if r["has_author"]]
    
    # Apply country filter if specified
    if country_filter:
        author_records = [r for r in author_records if r["country"] == country_filter]
        logger.info(f"Generating authors data for {country_filter}: {len(author_records)} records")
    else:
        logger.info(f"Generating global authors data: {len(author_records)} records")
    
    if not author_records:
        return {
            "authors": [],
            "total_authors": 0,
            "total_publications": 0,
            "country": country_filter,
            "generated_at": datetime.now().isoformat()
        }
    
    # Aggregate by author - use sets to track unique publications
    author_data = defaultdict(lambda: {
        "pub_ids": set(),  # Track unique publication IDs
        "types": defaultdict(int),
        "years": []
    })
    
    for record in author_records:
        author = record["author"]
        pub_id = record["pub_id"]
        ref_type = record["type"]
        year = record.get("year")
        
        # Only count each publication once per author
        if pub_id not in author_data[author]["pub_ids"]:
            author_data[author]["pub_ids"].add(pub_id)
            author_data[author]["types"][ref_type] += 1
            if year:
                author_data[author]["years"].append(year)
    
    # Build author list
    authors = []
    for author_name, data in author_data.items():
        author_entry = {
            "author": author_name,
            "publication_count": len(data["pub_ids"]),  # Count unique publications
            "types": dict(data["types"])
        }
        
        # Add year range if available
        if data["years"]:
            author_entry["earliest_year"] = min(data["years"])
            author_entry["latest_year"] = max(data["years"])
        
        authors.append(author_entry)
    
    # Sort by publication count (descending)
    authors.sort(key=lambda x: x["publication_count"], reverse=True)
    
    # Count total unique publications across all authors
    all_pub_ids = set()
    for data in author_data.values():
        all_pub_ids.update(data["pub_ids"])
    
    result = {
        "authors": authors,
        "total_authors": len(authors),
        "total_publications": len(all_pub_ids),  # Count unique publications
        "country": country_filter,
        "generated_at": datetime.now().isoformat()
    }
    
    return result


def generate_metadata(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate metadata about the references dataset."""
    year_records = [r for r in records if r["has_year"]]
    author_records = [r for r in records if r["has_author"]]
    
    years = [r["year"] for r in year_records]
    countries = set(r["country"] for r in records)
    ref_types = set(r["type"] for r in records)
    authors = set(r["author"] for r in author_records)
    
    # Count unique publications (not records)
    unique_pub_ids = set(r["pub_id"] for r in records)
    unique_pub_ids_with_year = set(r["pub_id"] for r in year_records)
    unique_pub_ids_with_author = set(r["pub_id"] for r in author_records)
    
    # Count by country
    country_counts = Counter(r["country"] for r in records)
    
    # Get countries with enough data for individual files (e.g., > 10 records)
    countries_with_files = sorted([
        country for country, count in country_counts.items() 
        if country != "Unknown" and count >= 10
    ])
    
    metadata = {
        "total_records": len(unique_pub_ids),
        "records_with_year": len(unique_pub_ids_with_year),
        "records_with_author": len(unique_pub_ids_with_author),
        "temporal": {
            "min_year": min(years) if years else None,
            "max_year": max(years) if years else None,
            "year_count": len(set(years)) if years else 0
        },
        "countries": {
            "count": len(countries),
            "values": sorted(countries),
            "with_individual_files": countries_with_files,
            "counts": dict(country_counts.most_common(20))
        },
        "reference_types": {
            "count": len(ref_types),
            "values": sorted(ref_types)
        },
        "authors": {
            "total_unique": len(authors),
            "total_publications": len(unique_pub_ids_with_author)
        },
        "files_generated": {
            "by_year_global": "references/by-year-global.json",
            "by_year_countries": [
                f"references/by-year-{country.lower().replace(' ', '-')}.json" 
                for country in countries_with_files
            ],
            "authors_global": "references/authors.json",
            "authors_countries": [
                f"references/authors-{country.lower().replace(' ', '-')}.json" 
                for country in countries_with_files
            ],
            "metadata": "references/metadata.json"
        },
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
    """Copy generated files to build/data/references directory."""
    build_dir = Path("build/data/references")
    if not build_dir.parent.exists():
        logger.info("build/data directory does not exist, skipping copy")
        return
    
    # Create build/data/references if it doesn't exist
    build_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Copying files to build/data/references directory...")
    import shutil
    
    for file in output_dir.glob("*.json"):
        dest = build_dir / file.name
        shutil.copy2(file, dest)
        logger.info(f"Copied {file.name} to build/data/references/")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate references visualizations JSONs from IWAC references subset"
    )
    parser.add_argument(
        "--output-dir",
        default="static/data/references",
        help="Directory to write JSON files (default: static/data/references)"
    )
    parser.add_argument(
        "--min-country-records",
        type=int,
        default=10,
        help="Minimum records per country to generate individual files (default: 10)"
    )
    
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    min_country_records = args.min_country_records
    
    # Load and process references data
    df = load_references_data()
    if df.empty:
        logger.error("No data loaded. Exiting.")
        return
    
    records = process_references_data(df)
    if not records:
        logger.error("No records processed. Exiting.")
        return
    
    # Generate global by-year data
    logger.info("Generating global by-year data...")
    by_year_global = generate_by_year_data(records)
    save_json(by_year_global, output_dir / "by-year-global.json")
    
    # Generate global authors data
    logger.info("Generating global authors data...")
    authors_global = generate_authors_data(records)
    save_json(authors_global, output_dir / "authors.json")
    
    # Get countries with enough data
    country_counts = Counter(r["country"] for r in records)
    countries_with_files = [
        country for country, count in country_counts.items()
        if country != "Unknown" and count >= min_country_records
    ]
    
    logger.info(f"Generating data for {len(countries_with_files)} countries with >={min_country_records} records")
    
    # Generate per-country data
    for country in countries_with_files:
        # By-year data
        by_year_country = generate_by_year_data(records, country)
        filename = f"by-year-{country.lower().replace(' ', '-')}.json"
        save_json(by_year_country, output_dir / filename)
        
        # Authors data
        authors_country = generate_authors_data(records, country)
        filename = f"authors-{country.lower().replace(' ', '-')}.json"
        save_json(authors_country, output_dir / filename)
    
    # Generate metadata
    logger.info("Generating metadata...")
    metadata = generate_metadata(records)
    save_json(metadata, output_dir / "metadata.json")
    
    # Copy to build directory if it exists
    copy_to_build_dir(output_dir)
    
    logger.info("✅ References data generation completed successfully!")
    logger.info(f"Generated files in {output_dir}:")
    logger.info(f"  - Global by-year: by-year-global.json")
    logger.info(f"  - Global authors: authors.json")
    logger.info(f"  - Country files: {len(countries_with_files)} × 2 (by-year + authors)")
    logger.info(f"  - Metadata: metadata.json")


if __name__ == "__main__":
    main()
