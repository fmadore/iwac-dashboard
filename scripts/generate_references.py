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


def normalize_publishers(value: Any) -> List[str]:
    """Normalize publisher field (multivalue separated by |)."""
    publishers = normalize_multivalue_field(value, "|")

    if not publishers:
        return []

    # Clean up publisher names and deduplicate
    cleaned_publishers = []
    seen = set()

    for publisher in publishers:
        # Remove extra whitespace
        publisher = " ".join(publisher.split())

        # Skip if empty or already seen
        if not publisher or publisher.lower() in seen:
            continue

        seen.add(publisher.lower())
        cleaned_publishers.append(publisher)

    return cleaned_publishers


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


def load_index_data() -> pd.DataFrame:
    """Load data from the index subset for author/publisher lookup."""
    logger.info(f"Loading index subset from {DATASET_ID}...")
    try:
        dset = load_dataset(DATASET_ID, "index")
        df: pd.DataFrame = dset["train"].to_pandas()
        logger.info(f"Loaded {len(df)} records from index subset")
        return df
    except Exception as e:
        logger.error(f"Failed to load index subset: {e}")
        return pd.DataFrame()


def build_name_to_id_lookup(index_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Build a lookup from entity names to their o:id and metadata.

    Returns a dict mapping normalized names to {o_id, original_name, type}.
    Includes both primary names (Titre) and alternative names (Titre alternatif).
    """
    if index_df.empty:
        return {}

    lookup: Dict[str, Dict[str, Any]] = {}

    # Find relevant columns
    id_col = None
    for col in ["o:id", "o_id", "id"]:
        if col in index_df.columns:
            id_col = col
            break

    title_col = None
    for col in ["Titre", "title", "Title"]:
        if col in index_df.columns:
            title_col = col
            break

    alt_title_col = None
    for col in ["Titre alternatif", "alternative_title"]:
        if col in index_df.columns:
            alt_title_col = col
            break

    type_col = None
    for col in ["Type", "type"]:
        if col in index_df.columns:
            type_col = col
            break

    if not id_col or not title_col:
        logger.warning(f"Could not find required columns in index. Found: {list(index_df.columns)}")
        return {}

    logger.info(f"Building name lookup from columns: id={id_col}, title={title_col}, alt={alt_title_col}, type={type_col}")

    for _, row in index_df.iterrows():
        o_id = row.get(id_col)
        if o_id is None or (isinstance(o_id, float) and pd.isna(o_id)):
            continue

        o_id = str(o_id).strip()
        entity_type = str(row.get(type_col, "")).strip() if type_col else ""

        # Get primary name
        title = row.get(title_col)
        if title and not (isinstance(title, float) and pd.isna(title)):
            title = str(title).strip()
            if title:
                # Normalize: lowercase, strip extra spaces
                normalized = " ".join(title.lower().split())
                if normalized not in lookup:
                    lookup[normalized] = {
                        "o_id": o_id,
                        "original_name": title,
                        "type": entity_type
                    }

        # Get alternative names
        if alt_title_col:
            alt_titles = row.get(alt_title_col)
            if alt_titles and not (isinstance(alt_titles, float) and pd.isna(alt_titles)):
                for alt in str(alt_titles).split("|"):
                    alt = alt.strip()
                    if alt:
                        normalized = " ".join(alt.lower().split())
                        if normalized not in lookup:
                            lookup[normalized] = {
                                "o_id": o_id,
                                "original_name": title if title else alt,
                                "type": entity_type
                            }

    logger.info(f"Built lookup with {len(lookup)} unique names")
    return lookup


def find_entity_id(name: str, lookup: Dict[str, Dict[str, Any]], entity_types: List[str] = None) -> Optional[str]:
    """Find the o:id for a given name.

    Args:
        name: The name to look up
        lookup: The name→id lookup dict
        entity_types: Optional list of entity types to filter by (e.g., ["Personnes", "Organisations"])

    Returns:
        The o:id if found, None otherwise
    """
    if not name or not lookup:
        return None

    normalized = " ".join(name.lower().split())

    entry = lookup.get(normalized)
    if entry:
        # Filter by type if specified
        if entity_types and entry["type"] not in entity_types:
            return None
        return entry["o_id"]

    return None


def parse_coordinates(coord_str: str) -> Optional[Tuple[float, float]]:
    """Parse coordinates from the Coordonnées field.

    Expected formats: "lat, lng" or "lat,lng"
    Returns (lat, lng) tuple or None if parsing fails.
    """
    if not coord_str or (isinstance(coord_str, float) and pd.isna(coord_str)):
        return None

    coord_str = str(coord_str).strip()
    if not coord_str:
        return None

    # Try common formats: "lat, lng" or "lat,lng"
    match = re.match(r'^(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)$', coord_str)
    if match:
        try:
            lat = float(match.group(1))
            lng = float(match.group(2))
            # Validate ranges
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return (lat, lng)
        except ValueError:
            pass

    return None


def build_coord_lookup(index_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Build a lookup from location names to their coordinates and metadata.

    Returns a dict mapping normalized names to {coordinates, original_name, o_id, type}.
    """
    if index_df.empty:
        return {}

    lookup: Dict[str, Dict[str, Any]] = {}

    # Find relevant columns
    title_col = None
    for col in ["Titre", "title", "Title"]:
        if col in index_df.columns:
            title_col = col
            break

    coord_col = None
    for col in ["Coordonnées", "coordinates", "coordonnees"]:
        if col in index_df.columns:
            coord_col = col
            break

    id_col = None
    for col in ["o:id", "o_id", "id"]:
        if col in index_df.columns:
            id_col = col
            break

    type_col = None
    for col in ["Type", "type"]:
        if col in index_df.columns:
            type_col = col
            break

    if not title_col or not coord_col:
        logger.warning(f"Could not find required columns. Found: {list(index_df.columns)}")
        return {}

    logger.info(f"Building coord lookup from columns: title={title_col}, coord={coord_col}, id={id_col}")

    entries_with_coords = 0

    for _, row in index_df.iterrows():
        title = row.get(title_col)
        if not title or (isinstance(title, float) and pd.isna(title)):
            continue

        coords = parse_coordinates(row.get(coord_col, ""))
        if not coords:
            continue

        title = str(title).strip()
        normalized = " ".join(title.lower().split())

        o_id = None
        if id_col:
            id_val = row.get(id_col)
            if id_val and not (isinstance(id_val, float) and pd.isna(id_val)):
                o_id = str(id_val).strip()

        entity_type = ""
        if type_col:
            type_val = row.get(type_col)
            if type_val and not (isinstance(type_val, float) and pd.isna(type_val)):
                entity_type = str(type_val).strip()

        if normalized not in lookup:
            lookup[normalized] = {
                "coordinates": coords,
                "original_name": title,
                "o_id": o_id,
                "type": entity_type
            }
            entries_with_coords += 1

    logger.info(f"Built coord lookup with {entries_with_coords} locations")
    return lookup


def generate_provenance_map_data(
    records: List[Dict[str, Any]],
    coord_lookup: Dict[str, Dict[str, Any]],
    name_lookup: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Generate provenance map data for references.

    Creates location markers with:
    - GPS coordinates
    - Publication count (for marker sizing)
    - List of linked publications
    """
    logger.info("Generating provenance map data...")

    # Aggregate publications by provenance location
    # Use pub_id to track unique publications per location
    location_data: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "pub_ids": set(),
        "publications": [],
        "types": defaultdict(int),
        "years": []
    })

    # Track unique publications for provenance extraction
    seen_pub_ids: Dict[str, Dict[str, Any]] = {}

    for record in records:
        pub_id = record["pub_id"]
        if pub_id in seen_pub_ids:
            continue

        # Get provenance from record (we need to add this to process_references_data)
        provenance_list = record.get("provenance_list", [])
        if not provenance_list:
            continue

        seen_pub_ids[pub_id] = {
            "title": record.get("title", ""),
            "type": record.get("type", "Unknown"),
            "year": record.get("year"),
            "authors": record.get("authors_list", [])
        }

        for provenance in provenance_list:
            normalized = " ".join(provenance.lower().split())

            # Check if we have coordinates for this location
            if normalized not in coord_lookup:
                continue

            if pub_id not in location_data[normalized]["pub_ids"]:
                location_data[normalized]["pub_ids"].add(pub_id)
                location_data[normalized]["types"][record.get("type", "Unknown")] += 1
                if record.get("year"):
                    location_data[normalized]["years"].append(record["year"])
                location_data[normalized]["publications"].append({
                    "pub_id": pub_id,
                    "title": record.get("title", ""),
                    "type": record.get("type", "Unknown"),
                    "year": record.get("year"),
                    "authors": record.get("authors_list", [])[:3]  # Limit to first 3 authors
                })

    logger.info(f"Found {len(location_data)} unique provenance locations with coordinates")

    if not location_data:
        return {
            "locations": [],
            "meta": {
                "totalLocations": 0,
                "totalPublications": 0,
                "generatedAt": datetime.now().isoformat()
            }
        }

    # Build location list with coordinates
    locations = []
    max_count = max(len(data["pub_ids"]) for data in location_data.values())

    for normalized, data in location_data.items():
        coord_entry = coord_lookup[normalized]
        lat, lng = coord_entry["coordinates"]

        location_entry = {
            "name": coord_entry["original_name"],
            "lat": lat,
            "lng": lng,
            "count": len(data["pub_ids"]),
            "countNorm": len(data["pub_ids"]) / max_count if max_count > 0 else 0,
            "types": dict(data["types"]),
            "publications": data["publications"][:50]  # Limit for popup display
        }

        # Add o_id if available
        if coord_entry.get("o_id"):
            location_entry["o_id"] = coord_entry["o_id"]

        # Add year range if available
        if data["years"]:
            location_entry["earliestYear"] = min(data["years"])
            location_entry["latestYear"] = max(data["years"])

        locations.append(location_entry)

    # Sort by count descending
    locations.sort(key=lambda x: x["count"], reverse=True)

    # Calculate bounds
    lats = [loc["lat"] for loc in locations]
    lngs = [loc["lng"] for loc in locations]

    result = {
        "locations": locations,
        "bounds": {
            "north": max(lats),
            "south": min(lats),
            "east": max(lngs),
            "west": min(lngs)
        } if locations else None,
        "meta": {
            "totalLocations": len(locations),
            "totalPublications": len(seen_pub_ids),
            "maxCount": max_count,
            "generatedAt": datetime.now().isoformat()
        }
    }

    return result


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
    publisher_col = find_column(["publisher", "Publisher", "editeur", "Editeur"])
    provenance_col = find_column(["provenance", "Provenance", "place", "Place", "lieu", "Lieu"])

    logger.info(f"Found columns: author={author_col}, country={country_col}, date={date_col}, type={type_col}, id={id_col}, publisher={publisher_col}, provenance={provenance_col}")
    
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

        # Extract publishers (can be multiple, pipe-separated)
        publishers = []
        if publisher_col:
            publishers = normalize_publishers(row.get(publisher_col))

        # Extract provenance locations (can be multiple, pipe-separated)
        provenance = []
        if provenance_col:
            provenance = normalize_multivalue_field(row.get(provenance_col), "|")

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
                        "publishers_list": publishers,  # Keep full list for publisher stats
                        "authors_list": authors,  # Keep full list for co-author network
                        "provenance_list": provenance,  # Keep full list for map
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
                            "publishers_list": publishers,
                            "authors_list": authors,  # Keep full list for co-author network
                            "provenance_list": provenance,  # Keep full list for map
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


def generate_authors_data(
    records: List[Dict[str, Any]],
    country_filter: Optional[str] = None,
    name_lookup: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
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
    matched_count = 0
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

        # Look up o:id from index (filter to Personnes type)
        if name_lookup:
            o_id = find_entity_id(author_name, name_lookup, ["Personnes"])
            if o_id:
                author_entry["o_id"] = o_id
                matched_count += 1

        authors.append(author_entry)

    # Sort by publication count (descending)
    authors.sort(key=lambda x: x["publication_count"], reverse=True)

    # Count total unique publications across all authors
    all_pub_ids = set()
    for data in author_data.values():
        all_pub_ids.update(data["pub_ids"])

    if name_lookup:
        logger.info(f"Matched {matched_count}/{len(authors)} authors to index entries")

    result = {
        "authors": authors,
        "total_authors": len(authors),
        "total_publications": len(all_pub_ids),  # Count unique publications
        "country": country_filter,
        "generated_at": datetime.now().isoformat()
    }

    return result


def generate_publishers_data(
    records: List[Dict[str, Any]],
    country_filter: Optional[str] = None,
    name_lookup: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Generate top publishers by publication count."""
    # Filter records with publishers (we need unique pub_ids per publisher)
    publisher_records = [r for r in records if r.get("publishers_list")]

    # Apply country filter if specified
    if country_filter:
        publisher_records = [r for r in publisher_records if r["country"] == country_filter]
        logger.info(f"Generating publishers data for {country_filter}: {len(publisher_records)} records")
    else:
        logger.info(f"Generating global publishers data: {len(publisher_records)} records")

    if not publisher_records:
        return {
            "publishers": [],
            "total_publishers": 0,
            "total_publications": 0,
            "country": country_filter,
            "generated_at": datetime.now().isoformat()
        }

    # Aggregate by publisher - use sets to track unique publications
    publisher_data = defaultdict(lambda: {
        "pub_ids": set(),  # Track unique publication IDs
        "types": defaultdict(int),
        "years": []
    })

    for record in publisher_records:
        publishers_list = record.get("publishers_list", [])
        pub_id = record["pub_id"]
        ref_type = record["type"]
        year = record.get("year")

        # Process each publisher in the list
        for publisher in publishers_list:
            # Only count each publication once per publisher
            if pub_id not in publisher_data[publisher]["pub_ids"]:
                publisher_data[publisher]["pub_ids"].add(pub_id)
                publisher_data[publisher]["types"][ref_type] += 1
                if year:
                    publisher_data[publisher]["years"].append(year)

    # Build publisher list
    publishers = []
    matched_count = 0
    for publisher_name, data in publisher_data.items():
        publisher_entry = {
            "publisher": publisher_name,
            "publication_count": len(data["pub_ids"]),  # Count unique publications
            "types": dict(data["types"])
        }

        # Add year range if available
        if data["years"]:
            publisher_entry["earliest_year"] = min(data["years"])
            publisher_entry["latest_year"] = max(data["years"])

        # Look up o:id from index (check all types - publishers can be Organisations, Personnes, etc.)
        if name_lookup:
            o_id = find_entity_id(publisher_name, name_lookup)  # No type filter
            if o_id:
                publisher_entry["o_id"] = o_id
                matched_count += 1

        publishers.append(publisher_entry)

    # Sort by publication count (descending)
    publishers.sort(key=lambda x: x["publication_count"], reverse=True)

    # Count total unique publications across all publishers
    all_pub_ids = set()
    for data in publisher_data.values():
        all_pub_ids.update(data["pub_ids"])

    if name_lookup:
        logger.info(f"Matched {matched_count}/{len(publishers)} publishers to index entries")

    result = {
        "publishers": publishers,
        "total_publishers": len(publishers),
        "total_publications": len(all_pub_ids),
        "country": country_filter,
        "generated_at": datetime.now().isoformat()
    }

    return result


def generate_coauthor_network(
    records: List[Dict[str, Any]],
    name_lookup: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Generate co-author network data.

    Creates a network where:
    - Nodes are authors
    - Edges connect authors who co-authored publications together
    - Edge weight is the number of co-authored publications
    """
    import hashlib

    logger.info("Generating co-author network...")

    # Build publication -> authors mapping (use unique pub_ids)
    pub_authors: Dict[str, set] = defaultdict(set)
    author_pubs: Dict[str, set] = defaultdict(set)

    for record in records:
        if not record.get("has_author"):
            continue

        pub_id = record["pub_id"]
        authors_list = record.get("authors_list", [])

        if len(authors_list) < 2:
            # Need at least 2 authors for co-authorship
            continue

        for author in authors_list:
            pub_authors[pub_id].add(author)
            author_pubs[author].add(pub_id)

    logger.info(f"Found {len(pub_authors)} publications with 2+ authors")

    # Build co-authorship edges
    edge_weights: Dict[tuple, Dict] = {}  # (author1, author2) -> {weight, pub_ids}

    for pub_id, authors in pub_authors.items():
        authors_list = sorted(authors)  # Sort for consistent edge keys

        # Create edges between all pairs of co-authors
        for i, author1 in enumerate(authors_list):
            for author2 in authors_list[i+1:]:
                edge_key = (author1, author2)

                if edge_key not in edge_weights:
                    edge_weights[edge_key] = {"weight": 0, "pub_ids": set()}

                edge_weights[edge_key]["weight"] += 1
                edge_weights[edge_key]["pub_ids"].add(pub_id)

    logger.info(f"Found {len(edge_weights)} unique co-author pairs")

    if not edge_weights:
        return {
            "nodes": [],
            "edges": [],
            "meta": {
                "generatedAt": datetime.now().isoformat(),
                "totalNodes": 0,
                "totalEdges": 0,
                "supportedTypes": ["author"],
                "weightMinConfigured": 1,
                "weightMinActual": 0,
                "weightMax": 0,
                "degree": {"min": 0, "max": 0, "mean": 0},
                "strength": {"min": 0, "max": 0, "mean": 0},
                "topLabelCount": 50,
                "typePairs": [["author", "author"]],
                "labelPriorityTop": []
            }
        }

    # Compute node metrics
    author_degree: Dict[str, int] = defaultdict(int)
    author_strength: Dict[str, int] = defaultdict(int)

    for (author1, author2), data in edge_weights.items():
        weight = data["weight"]
        author_degree[author1] += 1
        author_degree[author2] += 1
        author_strength[author1] += weight
        author_strength[author2] += weight

    # Get all authors that have co-authorships
    all_coauthors = set(author_degree.keys())

    # Build nodes
    def make_author_id(name: str) -> str:
        """Create a stable ID for an author."""
        hash_val = hashlib.md5(name.encode('utf-8')).hexdigest()[:8]
        return f"author:{hash_val}"

    # Sort authors by strength for label priority
    sorted_authors = sorted(all_coauthors, key=lambda a: author_strength[a], reverse=True)
    author_priority = {author: idx for idx, author in enumerate(sorted_authors)}

    nodes = []
    author_id_map = {}
    matched_count = 0

    for author in all_coauthors:
        author_id = make_author_id(author)
        author_id_map[author] = author_id

        node_data = {
            "id": author_id,
            "type": "author",
            "label": author,
            "count": len(author_pubs.get(author, set())),
            "degree": author_degree[author],
            "strength": author_strength[author],
            "labelPriority": author_priority[author]
        }

        # Look up o:id from index (filter to Personnes type for authors)
        if name_lookup:
            o_id = find_entity_id(author, name_lookup, ["Personnes"])
            if o_id:
                node_data["o_id"] = o_id
                matched_count += 1

        nodes.append(node_data)

    if name_lookup:
        logger.info(f"Matched {matched_count}/{len(nodes)} co-authors to index entries")

    # Build edges
    max_weight = max(data["weight"] for data in edge_weights.values())

    edges = []
    for (author1, author2), data in edge_weights.items():
        weight = data["weight"]
        edges.append({
            "source": author_id_map[author1],
            "target": author_id_map[author2],
            "type": "coauthor",
            "weight": weight,
            "weightNorm": weight / max_weight if max_weight > 0 else 0,
            "articleIds": list(data["pub_ids"])[:100]  # Limit to 100 for size
        })

    # Sort edges by weight descending
    edges.sort(key=lambda e: e["weight"], reverse=True)

    # Compute stats
    degrees = list(author_degree.values())
    strengths = list(author_strength.values())

    meta = {
        "generatedAt": datetime.now().isoformat(),
        "totalNodes": len(nodes),
        "totalEdges": len(edges),
        "supportedTypes": ["author"],
        "weightMinConfigured": 1,
        "weightMinActual": min(data["weight"] for data in edge_weights.values()),
        "weightMax": max_weight,
        "degree": {
            "min": min(degrees),
            "max": max(degrees),
            "mean": round(sum(degrees) / len(degrees), 2) if degrees else 0
        },
        "strength": {
            "min": min(strengths),
            "max": max(strengths),
            "mean": round(sum(strengths) / len(strengths), 2) if strengths else 0
        },
        "topLabelCount": min(50, len(nodes)),
        "typePairs": [["author", "author"]],
        "labelPriorityTop": [nodes[i]["label"] for i in range(min(50, len(nodes)))]
    }

    return {
        "nodes": nodes,
        "edges": edges,
        "meta": meta
    }


def generate_treemap_data(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate treemap data for country → reference type hierarchy.

    Creates a hierarchical structure:
    - Root: "References"
    - Level 1: Countries
    - Level 2: Reference types (leaf nodes with values)
    """
    logger.info("Generating treemap data (country → reference type)...")

    # Aggregate by country and type, tracking unique pub_ids
    country_type_pub_ids: Dict[str, Dict[str, set]] = defaultdict(lambda: defaultdict(set))

    for record in records:
        country = record["country"]
        ref_type = record["type"]
        pub_id = record["pub_id"]

        country_type_pub_ids[country][ref_type].add(pub_id)

    # Build hierarchical structure
    children = []
    total_count = 0

    for country in sorted(country_type_pub_ids.keys()):
        if country == "Unknown":
            continue  # Skip unknown country

        type_data = country_type_pub_ids[country]
        country_children = []
        country_total = 0

        for ref_type in sorted(type_data.keys()):
            count = len(type_data[ref_type])
            if count > 0:
                country_children.append({
                    "name": ref_type,
                    "value": count
                })
                country_total += count

        if country_children:
            children.append({
                "name": country,
                "children": country_children
            })
            total_count += country_total

    result = {
        "name": "References",
        "children": children,
        "meta": {
            "totalCountries": len(children),
            "totalReferences": total_count,
            "generatedAt": datetime.now().isoformat()
        }
    }

    logger.info(f"Generated treemap with {len(children)} countries, {total_count} references")
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
        "publishers": {
            "total_unique": len(set(p for r in records for p in r.get("publishers_list", []))),
            "total_publications": len(set(r["pub_id"] for r in records if r.get("publishers_list")))
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
            "publishers_global": "references/publishers.json",
            "publishers_countries": [
                f"references/publishers-{country.lower().replace(' ', '-')}.json"
                for country in countries_with_files
            ],
            "coauthor_network": "references/coauthor-network.json",
            "provenance_map": "references/provenance-map.json",
            "treemap": "references/treemap.json",
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

    # Load index data for name→id lookup
    index_df = load_index_data()
    name_lookup = build_name_to_id_lookup(index_df) if not index_df.empty else {}

    # Generate global by-year data
    logger.info("Generating global by-year data...")
    by_year_global = generate_by_year_data(records)
    save_json(by_year_global, output_dir / "by-year-global.json")

    # Generate global authors data
    logger.info("Generating global authors data...")
    authors_global = generate_authors_data(records, name_lookup=name_lookup)
    save_json(authors_global, output_dir / "authors.json")

    # Generate global publishers data
    logger.info("Generating global publishers data...")
    publishers_global = generate_publishers_data(records, name_lookup=name_lookup)
    save_json(publishers_global, output_dir / "publishers.json")

    # Generate co-author network
    logger.info("Generating co-author network...")
    coauthor_network = generate_coauthor_network(records, name_lookup=name_lookup)
    save_json(coauthor_network, output_dir / "coauthor-network.json")

    # Build coordinate lookup for provenance map
    coord_lookup = build_coord_lookup(index_df) if not index_df.empty else {}

    # Generate provenance map data
    logger.info("Generating provenance map data...")
    provenance_map = generate_provenance_map_data(records, coord_lookup, name_lookup)
    save_json(provenance_map, output_dir / "provenance-map.json")

    # Generate treemap data (country → reference type)
    logger.info("Generating treemap data...")
    treemap_data = generate_treemap_data(records)
    save_json(treemap_data, output_dir / "treemap.json")

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
        authors_country = generate_authors_data(records, country, name_lookup=name_lookup)
        filename = f"authors-{country.lower().replace(' ', '-')}.json"
        save_json(authors_country, output_dir / filename)

        # Publishers data
        publishers_country = generate_publishers_data(records, country, name_lookup=name_lookup)
        filename = f"publishers-{country.lower().replace(' ', '-')}.json"
        save_json(publishers_country, output_dir / filename)
    
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
    logger.info(f"  - Global publishers: publishers.json")
    logger.info(f"  - Co-author network: coauthor-network.json")
    logger.info(f"  - Provenance map: provenance-map.json")
    logger.info(f"  - Treemap: treemap.json")
    logger.info(f"  - Country files: {len(countries_with_files)} × 3 (by-year + authors + publishers)")
    logger.info(f"  - Metadata: metadata.json")


if __name__ == "__main__":
    main()
