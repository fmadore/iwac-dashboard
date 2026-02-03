#!/usr/bin/env python3
"""
IWAC World Map Data Generator

Generates world map visualization data from the IWAC Hugging Face dataset.

Data sources:
- 'index' subset: Contains location entities with coordinates (Coordonnées column)
- 'articles', 'documents', 'audiovisual', 'publications' subsets: Have 'spatial' field
  with pipe-separated location names that reference index entries

Process:
1. Load 'index' subset to get locations with their coordinates (Coordonnées)
2. Load article subsets to get spatial field references
3. Match spatial values to index locations to count articles per location
4. Generate location data with coordinates and article counts
5. Generate country-filtered and year-filtered data for interactive filtering

Output:
- static/data/world-map.json (main data with filtering support)
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from collections import defaultdict

try:
    from datasets import load_dataset
    import pandas as pd
except ImportError:
    print("Required packages not installed. Please run:")
    print("pip install datasets pandas huggingface-hub pyarrow")
    exit(1)

try:
    from shapely.geometry import Point, shape
    from shapely.prepared import prep
    HAS_SHAPELY = True
except ImportError:
    print("Warning: shapely not installed. Country detection from coordinates will be limited.")
    print("Install with: pip install shapely")
    HAS_SHAPELY = False

# Import shared utilities
from iwac_utils import (
    DATASET_ID,
    parse_coordinates,
    normalize_location_name,
    extract_year,
    find_column,
    save_json,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IWACWorldMapGenerator:
    """Generate world map data from IWAC dataset using index coordinates"""
    
    def __init__(self, output_dir: str = "static/data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Subsets with spatial field
        self.article_subsets = ['articles', 'documents', 'audiovisual', 'publications']
        
        # Data storage
        self.index_df = None  # Index subset with coordinates
        self.articles_data = []  # Combined articles data
        
        # Location lookup: normalized_name -> {name, coordinates, country, ...}
        self.location_lookup: Dict[str, Dict[str, Any]] = {}
        
        # World countries polygons for point-in-polygon lookup
        self.country_polygons: List[Dict[str, Any]] = []
    
    def load_world_countries(self) -> None:
        """Load world countries GeoJSON for point-in-polygon country detection."""
        if not HAS_SHAPELY:
            logger.warning("Shapely not available, skipping world countries loading")
            return
        
        geojson_path = Path("static/data/maps/world_countries.geojson")
        if not geojson_path.exists():
            logger.warning(f"World countries GeoJSON not found at {geojson_path}")
            return
        
        logger.info(f"Loading world countries from {geojson_path}...")
        
        try:
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geojson = json.load(f)
            
            for feature in geojson.get('features', []):
                props = feature.get('properties', {})
                # Try different property names for country name
                country_name = (
                    props.get('ADMIN') or 
                    props.get('name') or 
                    props.get('NAME') or 
                    props.get('name_long') or
                    props.get('sovereignt') or
                    ''
                )
                
                if not country_name:
                    continue
                
                try:
                    geom = shape(feature['geometry'])
                    prepared_geom = prep(geom)
                    self.country_polygons.append({
                        'name': country_name,
                        'geometry': geom,
                        'prepared': prepared_geom
                    })
                except Exception as e:
                    logger.debug(f"Error processing country {country_name}: {e}")
                    continue
            
            logger.info(f"Loaded {len(self.country_polygons)} country polygons")
            
        except Exception as e:
            logger.error(f"Error loading world countries GeoJSON: {e}")
    
    def find_country_for_coordinates(self, lat: float, lng: float) -> Optional[str]:
        """Find which country a coordinate point falls within."""
        if not HAS_SHAPELY or not self.country_polygons:
            return None
        
        point = Point(lng, lat)  # Note: shapely uses (x, y) = (lng, lat)
        
        for country in self.country_polygons:
            try:
                if country['prepared'].contains(point):
                    return country['name']
            except Exception:
                continue
        
        return None
        
    def fetch_index(self) -> None:
        """Fetch the index subset which contains location entities with coordinates."""
        logger.info("Fetching 'index' subset from Hugging Face...")
        
        try:
            dataset = load_dataset(DATASET_ID, "index")
            self.index_df = dataset['train'].to_pandas()
            logger.info(f"Loaded {len(self.index_df)} index entries")
            logger.info(f"Index columns: {list(self.index_df.columns)}")
        except Exception as e:
            logger.error(f"Error loading index subset: {e}")
            raise
    
    def fetch_articles(self) -> None:
        """Fetch all article subsets to get spatial references, country, and publication date."""
        logger.info("Fetching article subsets...")
        
        for subset_name in self.article_subsets:
            try:
                logger.info(f"Loading subset: {subset_name}")
                dataset = load_dataset(DATASET_ID, subset_name)
                df = dataset['train'].to_pandas()
                
                # Extract relevant fields
                for _, row in df.iterrows():
                    # Parse publication year
                    pub_date = row.get('pub_date', '')
                    year = extract_year(pub_date)
                    
                    # Get source country (from article's country field, not spatial location)
                    source_country = row.get('country', '')
                    if source_country and not pd.isna(source_country):
                        source_country = str(source_country).strip()
                    else:
                        source_country = ''
                    
                    article = {
                        'id': row.get('o:id', row.get('id', '')),
                        'spatial': row.get('spatial', row.get('dcterms:spatial', '')),
                        'source_country': source_country,  # Country where article was published
                        'year': year,  # Publication year
                        'subset': subset_name
                    }
                    self.articles_data.append(article)
                
                logger.info(f"Loaded {len(df)} records from {subset_name}")
                
            except Exception as e:
                logger.warning(f"Error loading subset {subset_name}: {e}")
                continue
        
        logger.info(f"Total articles loaded: {len(self.articles_data)}")
        
        # Log year range
        years = [a['year'] for a in self.articles_data if a['year']]
        if years:
            logger.info(f"Year range: {min(years)} - {max(years)}")
        
        # Log source countries
        source_countries = set(a['source_country'] for a in self.articles_data if a['source_country'])
        logger.info(f"Source countries: {sorted(source_countries)}")
    
    def build_location_lookup(self) -> None:
        """Build a lookup table from index entries that have coordinates."""
        logger.info("Building location lookup from index...")

        # Find the relevant columns using shared utility
        title_col = find_column(self.index_df, ['Titre', 'title', 'dcterms:title', 'name'])
        coord_col = find_column(self.index_df, ['Coordonnées', 'coordinates', 'coordonnees', 'curation:coordinates'])
        type_col = find_column(self.index_df, ['Type', 'type', "Type d'entité"])
        country_col = find_column(self.index_df, ['countries', 'country', 'pays'])

        logger.info(f"Using columns - Title: {title_col}, Coordinates: {coord_col}, Type: {type_col}, Country: {country_col}")
        
        if not title_col:
            logger.error("Could not find title column in index")
            return
        
        if not coord_col:
            logger.error("Could not find coordinates column in index")
            return
        
        locations_with_coords = 0
        locations_without_coords = 0
        
        for _, row in self.index_df.iterrows():
            # Only process location types
            if type_col:
                entity_type = str(row.get(type_col, '')).lower()
                if 'lieu' not in entity_type and 'location' not in entity_type:
                    continue
            
            title = row.get(title_col, '')
            if not title or pd.isna(title):
                continue
            
            coord_str = row.get(coord_col, '')
            coords = parse_coordinates(coord_str)
            
            if coords:
                locations_with_coords += 1
                normalized = normalize_location_name(title)
                
                # Determine country using point-in-polygon with world_countries.geojson
                country = self.find_country_for_coordinates(coords[0], coords[1])
                
                # Fallback to dataset country field if point-in-polygon fails
                if not country and country_col:
                    country_val = row.get(country_col, '')
                    if country_val and not pd.isna(country_val):
                        # Handle pipe-separated countries
                        if isinstance(country_val, str) and '|' in country_val:
                            country = country_val.split('|')[0].strip()
                        else:
                            country = str(country_val).strip()
                
                self.location_lookup[normalized] = {
                    'name': str(title).strip(),
                    'coordinates': coords,
                    'country': country if country else '',
                    'articleCount': 0,
                    'articleIds': set(),
                    'articleMeta': []  # Will store article metadata for filtering
                }
            else:
                locations_without_coords += 1
        
        logger.info(f"Built lookup with {locations_with_coords} locations having coordinates")
        logger.info(f"Skipped {locations_without_coords} locations without coordinates")
    
    def count_articles_per_location(self) -> None:
        """Count how many articles reference each location via spatial field.
        
        Also tracks article metadata (source country, year) for filtering.
        """
        logger.info("Counting articles per location...")
        
        matched = 0
        unmatched = 0
        unmatched_names = set()
        
        for article in self.articles_data:
            spatial = article.get('spatial', '')
            if not spatial or pd.isna(spatial):
                continue
            
            # Parse pipe-separated locations
            locations = []
            if isinstance(spatial, str):
                locations = [loc.strip() for loc in spatial.split('|') if loc.strip()]
            elif isinstance(spatial, (list, tuple)):
                locations = [str(loc).strip() for loc in spatial if loc]
            
            article_id = str(article.get('id', ''))
            source_country = article.get('source_country', '')
            year = article.get('year')
            
            for loc_name in locations:
                normalized = normalize_location_name(loc_name)
                
                if normalized in self.location_lookup:
                    self.location_lookup[normalized]['articleCount'] += 1
                    self.location_lookup[normalized]['articleIds'].add(article_id)
                    
                    # Track article metadata for filtering
                    self.location_lookup[normalized]['articleMeta'].append({
                        'id': article_id,
                        'source_country': source_country,
                        'year': year
                    })
                    matched += 1
                else:
                    unmatched += 1
                    if len(unmatched_names) < 50:  # Limit for logging
                        unmatched_names.add(loc_name)
        
        logger.info(f"Matched {matched} location references")
        logger.info(f"Unmatched {unmatched} location references")
        if unmatched_names:
            logger.debug(f"Sample unmatched locations: {list(unmatched_names)[:20]}")
    
    def generate_world_map_data(self) -> Dict[str, Any]:
        """Generate the final world map data structure with filtering support."""
        logger.info("Generating world map data...")
        
        # Build locations list
        locations_list = []
        
        # For choropleth: count UNIQUE articles per country
        # An article mentioning multiple locations in the same country counts as 1
        country_article_ids: Dict[str, set] = defaultdict(set)
        
        # Track all years and source countries for filtering
        all_years: set = set()
        all_source_countries: set = set()
        
        # Aggregated counts by source_country and year for filtering
        # Structure: { source_country: { year: count } }
        counts_by_source_country_year: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        
        # Location counts by source_country and year
        # Structure: { location_name: { source_country: { year: count } } }
        location_counts_by_filter: Dict[str, Dict[str, Dict[int, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )
        
        for normalized, data in self.location_lookup.items():
            if data['articleCount'] > 0:  # Only include locations with articles
                coords = data['coordinates']
                country = data['country']
                loc_name = data['name']
                
                locations_list.append({
                    'name': loc_name,
                    'lat': coords[0],
                    'lng': coords[1],
                    'articleCount': data['articleCount'],
                    'country': country if country else 'Unknown'
                })
                
                # Track unique article IDs per country for choropleth
                if country:
                    country_article_ids[country].update(data['articleIds'])
                
                # Process article metadata for filtering
                for meta in data.get('articleMeta', []):
                    source_country = meta.get('source_country', '')
                    year = meta.get('year')
                    
                    if source_country:
                        all_source_countries.add(source_country)
                    if year:
                        all_years.add(year)
                    
                    # Count by source country and year
                    if source_country and year:
                        counts_by_source_country_year[source_country][year] += 1
                        location_counts_by_filter[loc_name][source_country][year] += 1
                    elif source_country:
                        # Article with source country but no year
                        counts_by_source_country_year[source_country][0] += 1
                        location_counts_by_filter[loc_name][source_country][0] += 1
        
        # Convert to counts of unique articles per country
        country_counts = {
            country: len(article_ids) 
            for country, article_ids in country_article_ids.items()
        }
        
        # Sort by article count (descending)
        locations_list.sort(key=lambda x: x['articleCount'], reverse=True)
        
        # Build filter data for frontend
        sorted_years = sorted(y for y in all_years if y)
        sorted_source_countries = sorted(all_source_countries)
        
        # Convert counts_by_source_country_year to JSON-serializable format
        filter_counts = {}
        for src_country, year_counts in counts_by_source_country_year.items():
            filter_counts[src_country] = {str(y): c for y, c in year_counts.items()}
        
        # Convert location_counts_by_filter to JSON-serializable format
        location_filter_data = {}
        for loc_name, country_data in location_counts_by_filter.items():
            location_filter_data[loc_name] = {}
            for src_country, year_counts in country_data.items():
                location_filter_data[loc_name][src_country] = {str(y): c for y, c in year_counts.items()}
        
        # Build metadata
        total_locations = len(locations_list)
        total_unique_articles = len(set().union(*[data['articleIds'] for data in self.location_lookup.values() if data['articleIds']]))
        countries_with_data = sorted(set(
            loc['country'] for loc in locations_list if loc['country'] != 'Unknown'
        ))
        
        result = {
            'locations': locations_list,
            'countryCounts': country_counts,
            'filterData': {
                'sourceCountries': sorted_source_countries,
                'years': sorted_years,
                'yearRange': {
                    'min': min(sorted_years) if sorted_years else None,
                    'max': max(sorted_years) if sorted_years else None
                },
                'countsBySourceCountryYear': filter_counts,
                'locationCountsByFilter': location_filter_data
            },
            'metadata': {
                'totalLocations': total_locations,
                'totalArticles': total_unique_articles,
                'countriesWithData': countries_with_data,
                'sourceCountries': sorted_source_countries,
                'yearRange': {
                    'min': min(sorted_years) if sorted_years else None,
                    'max': max(sorted_years) if sorted_years else None
                },
                'generatedAt': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                'dataSource': DATASET_ID
            }
        }
        
        logger.info(f"Generated data for {total_locations} locations, {total_unique_articles} unique articles")
        logger.info(f"Countries with data: {len(countries_with_data)}")
        logger.info(f"Source countries: {sorted_source_countries}")
        logger.info(f"Year range: {min(sorted_years) if sorted_years else 'N/A'} - {max(sorted_years) if sorted_years else 'N/A'}")
        for country, count in sorted(country_counts.items(), key=lambda x: -x[1])[:10]:
            logger.info(f"  {country}: {count} articles")
        
        return result
    
    def save_data(self, data: Dict[str, Any]) -> None:
        """Save the generated data to JSON file."""
        output_path = self.output_dir / 'world-map.json'
        save_json(data, output_path, minify=True)
    
    def process(self) -> None:
        """Run the full data generation pipeline."""
        self.load_world_countries()  # Load GeoJSON for point-in-polygon
        self.fetch_index()
        self.fetch_articles()
        self.build_location_lookup()
        self.count_articles_per_location()
        data = self.generate_world_map_data()
        self.save_data(data)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate world map data from IWAC dataset'
    )
    parser.add_argument(
        '--output-dir', 
        default='static/data',
        help='Output directory for JSON files (default: static/data)'
    )
    
    args = parser.parse_args()
    
    generator = IWACWorldMapGenerator(output_dir=args.output_dir)
    generator.process()


if __name__ == "__main__":
    main()
