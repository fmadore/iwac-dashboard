#!/usr/bin/env python3
"""
IWAC Keywords Explorer Data Generator

Generates data for exploring Dublin Core Subject and Spatial Coverage fields
from the articles subdataset.

Output files:
- keywords-subjects.json: Subject keyword prevalence over time with facets
- keywords-spatial.json: Spatial coverage prevalence over time with facets
- keywords-metadata.json: Metadata including available filters

The data structure supports:
1. Top N keywords over time (line chart)
2. Custom keyword comparison
3. Filtering by country and newspaper
"""

from __future__ import annotations
import argparse
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


def parse_pipe_separated(value: Any) -> List[str]:
    """Parse pipe-separated values into a list of trimmed strings."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []

    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if str(v).strip()]

    value_str = str(value).strip()
    if not value_str:
        return []

    # Split by pipe and clean
    return [v.strip() for v in value_str.split('|') if v.strip()]


def extract_year(value: Any) -> Optional[int]:
    """Extract year from various date formats."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None

    try:
        if isinstance(value, (pd.Timestamp, datetime)):
            return value.year

        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            dt = pd.to_datetime(value, errors='coerce')
            if pd.notna(dt):
                return dt.year

        dt = pd.to_datetime(value, errors='coerce')
        if pd.notna(dt):
            return dt.year

    except Exception:
        pass

    return None


def normalize_country(value: Any) -> str:
    """Normalize country value to a standard string."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "Unknown"

    country_str = str(value).strip()
    if not country_str:
        return "Unknown"

    return country_str


def load_articles_data() -> pd.DataFrame:
    """Load articles data from the IWAC dataset."""
    logger.info("Loading articles subset from IWAC dataset...")
    try:
        dset = load_dataset(DATASET_ID, "articles")
        df = dset["train"].to_pandas()
        logger.info(f"Loaded {len(df)} articles")
        return df
    except Exception as e:
        logger.error(f"Error loading articles data: {e}")
        raise


def process_keywords_data(df: pd.DataFrame, field: str) -> Dict[str, Any]:
    """
    Process keywords (subject or spatial) and generate prevalence data.

    Returns a structure with:
    - global: yearly counts for all keywords globally
    - by_country: yearly counts faceted by country
    - by_newspaper: yearly counts faceted by newspaper
    - top_keywords: list of top keywords by total count
    - all_keywords: complete list of all keywords with counts
    """
    logger.info(f"Processing {field} keywords...")

    # Track keyword occurrences
    global_year_keyword = defaultdict(lambda: defaultdict(int))  # year -> keyword -> count
    country_year_keyword = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # country -> year -> keyword -> count
    newspaper_year_keyword = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # newspaper -> year -> keyword -> count

    keyword_total = Counter()  # keyword -> total count
    keyword_articles = defaultdict(set)  # keyword -> set of article indices

    countries_set: Set[str] = set()
    newspapers_set: Set[str] = set()
    years_set: Set[int] = set()

    for idx, row in df.iterrows():
        year = extract_year(row.get('pub_date'))
        if year is None:
            continue

        keywords = parse_pipe_separated(row.get(field))
        if not keywords:
            continue

        country = normalize_country(row.get('country'))
        newspaper = str(row.get('newspaper', '')).strip() or "Unknown"

        countries_set.add(country)
        newspapers_set.add(newspaper)
        years_set.add(year)

        for keyword in keywords:
            # Global counts
            global_year_keyword[year][keyword] += 1
            keyword_total[keyword] += 1
            keyword_articles[keyword].add(idx)

            # Country facet
            country_year_keyword[country][year][keyword] += 1

            # Newspaper facet
            newspaper_year_keyword[newspaper][year][keyword] += 1

    # Sort years
    sorted_years = sorted(years_set)

    # Get top keywords (by total count)
    top_keywords = [kw for kw, _ in keyword_total.most_common(100)]

    # Build global time series for top keywords
    global_series = {}
    for keyword in top_keywords:
        global_series[keyword] = {
            "years": sorted_years,
            "counts": [global_year_keyword[year].get(keyword, 0) for year in sorted_years],
            "total": keyword_total[keyword],
            "articles": len(keyword_articles[keyword])
        }

    # Build country-faceted data
    by_country = {}
    for country in sorted(countries_set):
        country_keywords = Counter()
        for year_data in country_year_keyword[country].values():
            for kw, count in year_data.items():
                country_keywords[kw] += count

        # Get top keywords for this country
        country_top = [kw for kw, _ in country_keywords.most_common(50)]

        by_country[country] = {
            "top_keywords": country_top,
            "series": {
                kw: {
                    "years": sorted_years,
                    "counts": [country_year_keyword[country][year].get(kw, 0) for year in sorted_years]
                }
                for kw in country_top
            },
            "total_keywords": len(country_keywords)
        }

    # Build newspaper-faceted data
    by_newspaper = {}
    for newspaper in sorted(newspapers_set):
        newspaper_keywords = Counter()
        for year_data in newspaper_year_keyword[newspaper].values():
            for kw, count in year_data.items():
                newspaper_keywords[kw] += count

        # Get top keywords for this newspaper
        newspaper_top = [kw for kw, _ in newspaper_keywords.most_common(50)]

        by_newspaper[newspaper] = {
            "top_keywords": newspaper_top,
            "series": {
                kw: {
                    "years": sorted_years,
                    "counts": [newspaper_year_keyword[newspaper][year].get(kw, 0) for year in sorted_years]
                }
                for kw in newspaper_top
            },
            "total_keywords": len(newspaper_keywords)
        }

    # All keywords with metadata
    all_keywords = [
        {
            "keyword": kw,
            "total": count,
            "articles": len(keyword_articles[kw])
        }
        for kw, count in keyword_total.most_common()
    ]

    logger.info(f"Processed {len(keyword_total)} unique {field} keywords across {len(sorted_years)} years")

    return {
        "field": field,
        "years": sorted_years,
        "top_keywords": top_keywords[:20],  # Top 20 for default display
        "global_series": global_series,
        "by_country": by_country,
        "by_newspaper": by_newspaper,
        "all_keywords": all_keywords,
        "stats": {
            "total_keywords": len(keyword_total),
            "total_occurrences": sum(keyword_total.values()),
            "year_range": [min(sorted_years), max(sorted_years)] if sorted_years else None,
            "countries_count": len(countries_set),
            "newspapers_count": len(newspapers_set)
        }
    }


def generate_metadata(df: pd.DataFrame, subjects_data: Dict, spatial_data: Dict) -> Dict[str, Any]:
    """Generate metadata about the keywords dataset."""

    # Get unique countries and newspapers
    countries = sorted(set(
        normalize_country(row.get('country'))
        for _, row in df.iterrows()
    ))

    newspapers = sorted(set(
        str(row.get('newspaper', '')).strip() or "Unknown"
        for _, row in df.iterrows()
    ))

    # Remove 'Unknown' if present and add at end
    if "Unknown" in countries:
        countries.remove("Unknown")
        countries.append("Unknown")
    if "Unknown" in newspapers:
        newspapers.remove("Unknown")
        newspapers.append("Unknown")

    return {
        "total_articles": len(df),
        "countries": countries,
        "newspapers": newspapers,
        "subjects": {
            "total_keywords": subjects_data["stats"]["total_keywords"],
            "total_occurrences": subjects_data["stats"]["total_occurrences"],
            "top_5": subjects_data["top_keywords"][:5]
        },
        "spatial": {
            "total_keywords": spatial_data["stats"]["total_keywords"],
            "total_occurrences": spatial_data["stats"]["total_occurrences"],
            "top_5": spatial_data["top_keywords"][:5]
        },
        "year_range": subjects_data["stats"]["year_range"],
        "generated_at": datetime.now().isoformat()
    }


def save_json(data: Any, path: Path) -> None:
    """Save data to JSON file with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    try:
        size_kb = path.stat().st_size / 1024
        logger.info(f"Wrote {path} ({size_kb:.1f} KB)")
    except Exception:
        logger.info(f"Wrote {path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate keywords data from IWAC articles dataset")
    parser.add_argument(
        "--output-dir",
        default="static/data",
        help="Directory to write JSON files (default: static/data)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    logger.info("=" * 60)
    logger.info("IWAC Keywords Explorer Data Generator")
    logger.info("=" * 60)

    try:
        # Load articles data
        df = load_articles_data()

        # Process subject keywords
        subjects_data = process_keywords_data(df, "subject")
        save_json(subjects_data, output_dir / "keywords-subjects.json")

        # Process spatial keywords
        spatial_data = process_keywords_data(df, "spatial")
        save_json(spatial_data, output_dir / "keywords-spatial.json")

        # Generate metadata
        metadata = generate_metadata(df, subjects_data, spatial_data)
        save_json(metadata, output_dir / "keywords-metadata.json")

        logger.info("\n" + "=" * 60)
        logger.info("Keywords data generation completed successfully!")
        logger.info("=" * 60)

        # Summary
        logger.info(f"\nSummary:")
        logger.info(f"  - Total articles processed: {len(df)}")
        logger.info(f"  - Subject keywords: {subjects_data['stats']['total_keywords']}")
        logger.info(f"  - Spatial keywords: {spatial_data['stats']['total_keywords']}")
        logger.info(f"  - Countries: {len(metadata['countries'])}")
        logger.info(f"  - Newspapers: {len(metadata['newspapers'])}")

        # Copy to build directory if it exists
        build_dir = Path("build/data")
        if build_dir.exists():
            logger.info("\nCopying files to build/data...")
            for file in ["keywords-subjects.json", "keywords-spatial.json", "keywords-metadata.json"]:
                src = output_dir / file
                dst = build_dir / file
                if src.exists():
                    dst.write_bytes(src.read_bytes())
                    logger.info(f"Copied {file} to build/data")

    except Exception as e:
        logger.error(f"Keywords data generation failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
