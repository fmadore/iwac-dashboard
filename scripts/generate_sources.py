#!/usr/bin/env python3
"""
IWAC Sources Data Generator

Generates sources (newspapers/publications) data from the IWAC Hugging Face dataset
with geographic coordinates for map visualization.

Data sources:
- 'articles', 'documents', 'audiovisual', 'publications' subsets: Have 'source' field
  containing newspaper/publication names
- 'index' subset: Contains location entities with 'Titre' and 'Coordonnées' (GPS) columns

Process:
1. Load all content subsets (except index and references)
2. Extract and count 'source' field values
3. Load index subset to get coordinate mappings
4. Match source names to index 'Titre' to retrieve GPS coordinates
5. Generate sources data with coordinates for map visualization

Output: 
- static/data/sources.json (main data with sources, counts, and coordinates)
"""

import json
import argparse
import logging
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from collections import defaultdict

try:
    from datasets import load_dataset
    import pandas as pd
except ImportError:
    print("Required packages not installed. Please run:")
    print("pip install datasets pandas huggingface-hub pyarrow")
    exit(1)


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


DATASET_ID = "fmadore/islam-west-africa-collection"

# Custom coordinate overrides for sources not in the index
# Format: source_name -> (lat, lng)
CUSTOM_COORDINATES = {
    "Wayback Machine": (37.782320470033035, -122.47163767055227),
    "Centre de Recherche et d'Action pour la Paix": (5.33977337625783, -4.000600603778056),
    "La Nation": (6.35690531508226, 2.4017090109401797),
    "Frédérick Madore": (52.516667, 13.383333),
    "Cercle d'Études, de Recherches et de Formation Islamiques": (12.359473717928248, -1.4978785755133803),
    "Abdoulaye Sounaye": (52.427976, 13.202396),
    "Louis Audet Gosselin": (45.503343, -73.586841),
}


def parse_coordinates(coord_str: str) -> Optional[Tuple[float, float]]:
    """
    Parse coordinates from the Coordonnées field.
    Expected formats: "lat, lng" or "lat,lng" or similar
    Returns (lat, lng) tuple or None if parsing fails.
    """
    if not coord_str or pd.isna(coord_str):
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


def normalize_name(name: str) -> str:
    """Normalize a name for matching (lowercase, stripped, unicode normalized)."""
    if not name:
        return ""
    # Lowercase, strip whitespace, normalize unicode
    name = unicodedata.normalize('NFC', str(name).strip().lower())
    return name


class IWACSourcesGenerator:
    """Generate sources data from IWAC dataset with GPS coordinates"""
    
    def __init__(self, output_dir: str = "static/data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Content subsets with source field
        self.content_subsets = ['articles', 'publications', 'documents', 'audiovisual']
        
        # Data storage
        self.index_df = None  # Index subset with coordinates
        self.sources_data: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'by_type': defaultdict(int),
            'countries': set()
        })
        
        # Coordinate lookup: normalized_title -> {name, coordinates, id}
        self.coord_lookup: Dict[str, Dict[str, Any]] = {}
    
    def fetch_index(self) -> None:
        """Fetch the index subset which may contain source entities with coordinates."""
        logger.info("Fetching 'index' subset from Hugging Face...")
        
        try:
            dataset = load_dataset(DATASET_ID, "index")
            self.index_df = dataset['train'].to_pandas()
            logger.info(f"Loaded {len(self.index_df)} index entries")
            logger.info(f"Index columns: {list(self.index_df.columns)}")
        except Exception as e:
            logger.error(f"Error loading index subset: {e}")
            raise
    
    def build_coord_lookup(self) -> None:
        """Build a lookup table from index entries that have coordinates."""
        logger.info("Building coordinate lookup from index...")
        
        # Find the relevant columns
        title_col = None
        for col in ['Titre', 'title', 'dcterms:title', 'name']:
            if col in self.index_df.columns:
                title_col = col
                break
        
        coord_col = None
        for col in ['Coordonnées', 'coordinates', 'coordonnees', 'curation:coordinates']:
            if col in self.index_df.columns:
                coord_col = col
                break
        
        # Find the o:id column
        id_col = None
        for col in ['o:id', 'o_id', 'id', 'ID']:
            if col in self.index_df.columns:
                id_col = col
                break
        
        logger.info(f"Using columns - Title: {title_col}, Coordinates: {coord_col}, ID: {id_col}")
        
        if not title_col:
            logger.warning("Could not find title column in index")
            return
        
        if not coord_col:
            logger.warning("Could not find coordinates column in index")
            return
        
        entries_with_coords = 0
        
        for _, row in self.index_df.iterrows():
            title = row.get(title_col, '')
            if not title or pd.isna(title):
                continue
            
            coord_str = row.get(coord_col, '')
            coords = parse_coordinates(coord_str)
            
            if coords:
                entries_with_coords += 1
                normalized = normalize_name(title)
                
                # Get the o:id if available
                oid = None
                if id_col:
                    oid_val = row.get(id_col, '')
                    if oid_val and not pd.isna(oid_val):
                        try:
                            oid = int(oid_val)
                        except (ValueError, TypeError):
                            oid = str(oid_val).strip() if oid_val else None
                
                self.coord_lookup[normalized] = {
                    'name': str(title).strip(),
                    'coordinates': coords,
                    'id': oid
                }
        
        logger.info(f"Built lookup with {entries_with_coords} entries having coordinates")
    
    def fetch_and_process_sources(self) -> None:
        """Fetch all content subsets and extract source data."""
        logger.info("Fetching content subsets and extracting sources...")
        
        for subset_name in self.content_subsets:
            try:
                logger.info(f"Loading subset: {subset_name}")
                dataset = load_dataset(DATASET_ID, subset_name)
                df = dataset['train'].to_pandas()
                
                logger.info(f"Loaded {len(df)} records from {subset_name}")
                logger.info(f"Columns: {list(df.columns)}")
                
                # Find source column
                source_col = None
                for col in ['source', 'dcterms:source', 'newspaper']:
                    if col in df.columns:
                        source_col = col
                        break
                
                if not source_col:
                    logger.warning(f"No source column found in {subset_name}")
                    continue
                
                # Find country column
                country_col = None
                for col in ['country', 'pays']:
                    if col in df.columns:
                        country_col = col
                        break
                
                # Process each record
                for _, row in df.iterrows():
                    source = row.get(source_col, '')
                    if not source or pd.isna(source):
                        continue
                    
                    source = str(source).strip()
                    if not source:
                        continue
                    
                    # Get country if available
                    country = ''
                    if country_col:
                        country_val = row.get(country_col, '')
                        if country_val and not pd.isna(country_val):
                            country = str(country_val).strip()
                    
                    # Update source data
                    self.sources_data[source]['count'] += 1
                    self.sources_data[source]['by_type'][subset_name] += 1
                    if country:
                        self.sources_data[source]['countries'].add(country)
                
                logger.info(f"Processed {len(df)} records from {subset_name}")
                
            except Exception as e:
                logger.warning(f"Error loading subset {subset_name}: {e}")
                continue
        
        logger.info(f"Total unique sources found: {len(self.sources_data)}")
    
    def generate_sources_json(self) -> Dict[str, Any]:
        """Generate the final sources data structure."""
        logger.info("Generating sources JSON data...")
        
        sources_list = []
        sources_with_coords = 0
        sources_without_coords = 0
        total_items = 0
        
        for source_name, data in self.sources_data.items():
            total_items += data['count']
            
            # Try to find coordinates
            normalized = normalize_name(source_name)
            coord_data = self.coord_lookup.get(normalized)
            
            source_entry = {
                'name': source_name,
                'count': data['count'],
                'byType': dict(data['by_type']),
                'countries': sorted(data['countries'])
            }
            
            if coord_data:
                source_entry['lat'] = coord_data['coordinates'][0]
                source_entry['lng'] = coord_data['coordinates'][1]
                if coord_data.get('id'):
                    source_entry['id'] = coord_data['id']
                sources_with_coords += 1
            elif source_name in CUSTOM_COORDINATES:
                # Use custom override coordinates
                custom_coords = CUSTOM_COORDINATES[source_name]
                source_entry['lat'] = custom_coords[0]
                source_entry['lng'] = custom_coords[1]
                sources_with_coords += 1
            else:
                sources_without_coords += 1
            
            sources_list.append(source_entry)
        
        # Sort by count descending
        sources_list.sort(key=lambda x: x['count'], reverse=True)
        
        # Calculate stats by type
        type_totals = defaultdict(int)
        for source in sources_list:
            for doc_type, count in source['byType'].items():
                type_totals[doc_type] += count
        
        # Get unique countries
        all_countries = set()
        for source in sources_list:
            all_countries.update(source['countries'])
        
        result = {
            'sources': sources_list,
            'metadata': {
                'totalSources': len(sources_list),
                'sourcesWithCoordinates': sources_with_coords,
                'sourcesWithoutCoordinates': sources_without_coords,
                'totalItems': total_items,
                'byType': dict(type_totals),
                'countries': sorted(all_countries),
                'generatedAt': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                'dataSource': DATASET_ID
            }
        }
        
        logger.info(f"Generated data for {len(sources_list)} sources")
        logger.info(f"  - With coordinates: {sources_with_coords}")
        logger.info(f"  - Without coordinates: {sources_without_coords}")
        logger.info(f"  - Total items: {total_items}")
        
        return result
    
    def save_data(self, data: Dict[str, Any]) -> None:
        """Save the generated data to JSON file."""
        output_path = self.output_dir / 'sources.json'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved sources data to {output_path}")
    
    def process(self) -> None:
        """Run the full data generation pipeline."""
        self.fetch_index()
        self.build_coord_lookup()
        self.fetch_and_process_sources()
        data = self.generate_sources_json()
        self.save_data(data)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate sources data from IWAC dataset'
    )
    parser.add_argument(
        '--output-dir', 
        default='static/data',
        help='Output directory for JSON files (default: static/data)'
    )
    
    args = parser.parse_args()
    
    generator = IWACSourcesGenerator(output_dir=args.output_dir)
    generator.process()
    logger.info("✅ Sources data generation completed successfully!")


if __name__ == "__main__":
    main()
