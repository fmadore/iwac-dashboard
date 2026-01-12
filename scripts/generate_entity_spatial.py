#!/usr/bin/env python3
"""
IWAC Entity Spatial Data Generator

Generates entity-location-article mapping data for the IWAC Dashboard.
This data enables the entity spatial visualization showing where entities
(persons, events, topics, organisations) appear geographically.

Output Structure (one JSON file per entity for optimal lazy loading):
- static/data/entity-spatial/index.json - Entity summaries for picker (~200-400KB)
- static/data/entity-spatial/Personnes/{entity_id}.json - Individual person details
- static/data/entity-spatial/Événements/{entity_id}.json - Individual event details
- static/data/entity-spatial/Sujets/{entity_id}.json - Individual topic details
- static/data/entity-spatial/Organisations/{entity_id}.json - Individual org details

Each entity file is typically 1-50KB, loaded only when that entity is selected.
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timezone
from collections import defaultdict
import unicodedata
import re

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

# Entity types to include (French labels from dataset)
INCLUDED_ENTITY_TYPES = {
    "Personnes",      # Persons
    "Événements",     # Events
    "Sujets",         # Topics (subjects)
    "Organisations",  # Organizations
}

# Type mapping for i18n
TYPE_LABELS = {
    "Personnes": {"en": "Persons", "fr": "Personnes"},
    "Événements": {"en": "Events", "fr": "Événements"},
    "Sujets": {"en": "Topics", "fr": "Sujets"},
    "Organisations": {"en": "Organizations", "fr": "Organisations"},
}


def normalize_name(name: str) -> str:
    """Normalize a name for matching."""
    if not name:
        return ""
    name = unicodedata.normalize('NFC', str(name).strip().lower())
    name = ' '.join(name.split())
    return name


def parse_pipe_separated(value: Any) -> List[str]:
    """Parse a pipe-separated string into a list of values."""
    if not value or pd.isna(value):
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if v and str(v).strip()]
    s = str(value).strip()
    if not s:
        return []
    return [part.strip() for part in s.split('|') if part.strip()]


class EntitySpatialGenerator:
    """Generate entity-location-article mapping data."""

    def __init__(self, output_dir: str = "static/data"):
        self.output_dir = Path(output_dir) / "entity-spatial"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Article subsets to process
        self.article_subsets = ['articles', 'publications']

        # Data storage
        self.index_df = None
        self.articles_data: List[Dict] = []

        # Entity lookup: normalized_name -> entity_info
        self.entity_lookup: Dict[str, Dict] = {}
        # Entity ID -> entity_info
        self.entity_by_id: Dict[int, Dict] = {}

        # Location lookup: normalized_name -> {name, lat, lng, country}
        self.location_lookup: Dict[str, Dict] = {}

        # Result: entity_id -> {locations: {loc_name: {articles: [...]}}}
        self.entity_spatial: Dict[int, Dict] = defaultdict(lambda: {
            'locations': defaultdict(lambda: {'articles': [], 'article_ids': set()})
        })

    def load_location_coordinates(self) -> None:
        """Load location coordinates from world-map.json."""
        world_map_path = Path("static/data") / 'world-map.json'

        if not world_map_path.exists():
            logger.warning(f"world-map.json not found at {world_map_path}")
            return

        logger.info(f"Loading location coordinates from {world_map_path}...")

        try:
            with open(world_map_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for loc in data.get('locations', []):
                name = loc.get('name', '')
                if name:
                    normalized = normalize_name(name)
                    self.location_lookup[normalized] = {
                        'name': name,
                        'lat': loc.get('lat', 0),
                        'lng': loc.get('lng', 0),
                        'country': loc.get('country', 'Unknown')
                    }

            logger.info(f"Loaded {len(self.location_lookup)} location coordinates")

        except Exception as e:
            logger.error(f"Error loading world-map.json: {e}")

    def fetch_index(self) -> None:
        """Fetch the index subset which contains entity data."""
        logger.info("Fetching 'index' subset from Hugging Face...")

        try:
            dataset = load_dataset(DATASET_ID, "index")
            self.index_df = dataset['train'].to_pandas()
            logger.info(f"Loaded {len(self.index_df)} index entries")
        except Exception as e:
            logger.error(f"Error loading index subset: {e}")
            raise

    def fetch_articles(self) -> None:
        """Fetch article subsets to get subject and spatial references."""
        logger.info("Fetching article subsets...")

        for subset_name in self.article_subsets:
            try:
                logger.info(f"Loading subset: {subset_name}")
                dataset = load_dataset(DATASET_ID, subset_name)
                df = dataset['train'].to_pandas()

                for _, row in df.iterrows():
                    article_id = row.get('o:id', row.get('id', ''))
                    if pd.isna(article_id):
                        continue
                    article_id = str(article_id)

                    title = row.get('dcterms:title', row.get('title', ''))
                    if pd.isna(title):
                        title = ''

                    pub_date = row.get('pub_date', '')
                    if pd.isna(pub_date):
                        pub_date = ''

                    newspaper = row.get('newspaper', '')
                    if pd.isna(newspaper):
                        newspaper = ''

                    country = row.get('country', '')
                    if pd.isna(country):
                        country = ''

                    subject = row.get('subject', '')
                    spatial = row.get('dcterms:spatial', row.get('spatial', ''))

                    self.articles_data.append({
                        'id': article_id,
                        'title': str(title).strip() if title else '',
                        'pub_date': str(pub_date).strip() if pub_date else '',
                        'newspaper': str(newspaper).strip() if newspaper else '',
                        'country': str(country).strip() if country else '',
                        'subject': subject,
                        'spatial': spatial,
                        'subset': subset_name
                    })

                logger.info(f"Loaded {len(df)} records from {subset_name}")

            except Exception as e:
                logger.warning(f"Error loading subset {subset_name}: {e}")
                continue

        logger.info(f"Total articles loaded: {len(self.articles_data)}")

    def build_entity_lookup(self) -> None:
        """Build lookup tables from index entities."""
        logger.info("Building entity lookup...")

        id_col = None
        for col in ['o:id', 'id', 'ID']:
            if col in self.index_df.columns:
                id_col = col
                break

        title_col = None
        for col in ['Titre', 'dcterms:title', 'title']:
            if col in self.index_df.columns:
                title_col = col
                break

        type_col = None
        for col in ['Type', 'type']:
            if col in self.index_df.columns:
                type_col = col
                break

        freq_col = None
        for col in ['frequency', 'occurrences']:
            if col in self.index_df.columns:
                freq_col = col
                break

        first_col = None
        for col in ['first_occurrence', 'firstOccurrence']:
            if col in self.index_df.columns:
                first_col = col
                break

        last_col = None
        for col in ['last_occurrence', 'lastOccurrence']:
            if col in self.index_df.columns:
                last_col = col
                break

        if not id_col or not title_col or not type_col:
            logger.error("Could not find required columns in index")
            return

        included_count = 0

        for _, row in self.index_df.iterrows():
            entity_type = row.get(type_col, '')
            if pd.isna(entity_type):
                continue
            entity_type = str(entity_type).strip()

            if entity_type not in INCLUDED_ENTITY_TYPES:
                continue

            entity_id = row.get(id_col)
            if pd.isna(entity_id):
                continue
            try:
                entity_id = int(entity_id)
            except (ValueError, TypeError):
                continue

            title = row.get(title_col, '')
            if pd.isna(title) or not title:
                continue
            title = str(title).strip()

            frequency = 0
            if freq_col and not pd.isna(row.get(freq_col)):
                try:
                    frequency = int(row.get(freq_col))
                except (ValueError, TypeError):
                    pass

            first_date = ''
            if first_col and not pd.isna(row.get(first_col)):
                first_date = str(row.get(first_col)).strip()

            last_date = ''
            if last_col and not pd.isna(row.get(last_col)):
                last_date = str(row.get(last_col)).strip()

            entity_info = {
                'id': entity_id,
                'name': title,
                'type': entity_type,
                'frequency': frequency,
                'first_occurrence': first_date,
                'last_occurrence': last_date
            }

            normalized = normalize_name(title)
            self.entity_lookup[normalized] = entity_info
            self.entity_by_id[entity_id] = entity_info

            included_count += 1

        logger.info(f"Built entity lookup with {included_count} entities")

    def process_articles(self) -> None:
        """Process articles to build entity-location-article mapping."""
        logger.info("Processing articles to build entity-location mapping...")

        matched_entities = 0

        for article in self.articles_data:
            subjects = parse_pipe_separated(article['subject'])
            if not subjects:
                continue

            locations = parse_pipe_separated(article['spatial'])

            for subject in subjects:
                normalized_subject = normalize_name(subject)

                entity = self.entity_lookup.get(normalized_subject)
                if not entity:
                    continue

                matched_entities += 1
                entity_id = entity['id']

                if locations:
                    for loc_name in locations:
                        normalized_loc = normalize_name(loc_name)

                        loc_data = self.entity_spatial[entity_id]['locations'][normalized_loc]
                        if article['id'] in loc_data['article_ids']:
                            continue

                        loc_data['article_ids'].add(article['id'])

                        coords = self.location_lookup.get(normalized_loc, {})

                        loc_data['articles'].append({
                            'id': article['id'],
                            'title': article['title'],
                            'date': article['pub_date'],
                            'newspaper': article['newspaper'],
                            'country': article['country'],
                            'type': article['subset']
                        })

                        if 'name' not in loc_data:
                            loc_data['name'] = coords.get('name', loc_name)
                            loc_data['lat'] = coords.get('lat', 0)
                            loc_data['lng'] = coords.get('lng', 0)
                            loc_data['location_country'] = coords.get('country', 'Unknown')

        logger.info(f"Matched {matched_entities} entity mentions")

    def generate_output(self) -> None:
        """Generate individual output files per entity."""
        logger.info("Generating individual entity files...")

        # Build index (summaries) and prepare entity details
        index_data: Dict[str, List[Dict]] = {t: [] for t in INCLUDED_ENTITY_TYPES}

        # Create subdirectories for each entity type
        for entity_type in INCLUDED_ENTITY_TYPES:
            type_dir = self.output_dir / entity_type
            type_dir.mkdir(parents=True, exist_ok=True)

        entities_with_locations = 0
        total_files_size = 0

        for entity_id, entity in self.entity_by_id.items():
            entity_type = entity['type']
            spatial_data = self.entity_spatial.get(entity_id, {'locations': {}})

            # Build location list
            all_article_ids: Set[str] = set()
            location_countries: Set[str] = set()
            all_dates: List[str] = []
            locations_list = []

            for loc_normalized, loc_data in spatial_data['locations'].items():
                if not loc_data['articles']:
                    continue

                location_entry = {
                    'name': loc_data.get('name', loc_normalized),
                    'lat': loc_data.get('lat', 0),
                    'lng': loc_data.get('lng', 0),
                    'country': loc_data.get('location_country', 'Unknown'),
                    'articleCount': len(loc_data['articles']),
                    'articles': loc_data['articles']
                }

                locations_list.append(location_entry)

                for art in loc_data['articles']:
                    all_article_ids.add(art['id'])
                    if art['date']:
                        all_dates.append(art['date'])

                if location_entry['country'] and location_entry['country'] != 'Unknown':
                    location_countries.add(location_entry['country'])

            locations_list.sort(key=lambda x: x['articleCount'], reverse=True)

            date_range = {'first': '', 'last': ''}
            if all_dates:
                sorted_dates = sorted(all_dates)
                date_range = {'first': sorted_dates[0], 'last': sorted_dates[-1]}

            # Add to index (summary only)
            index_data[entity_type].append({
                'id': entity_id,
                'name': entity['name'],
                'articleCount': len(all_article_ids),
                'locationCount': len(locations_list)
            })

            # Save individual entity file (only if has location data)
            if locations_list:
                entity_detail = {
                    'id': entity_id,
                    'name': entity['name'],
                    'type': entity_type,
                    'stats': {
                        'articleCount': len(all_article_ids),
                        'countries': sorted(location_countries),
                        'dateRange': date_range
                    },
                    'locations': locations_list
                }

                entity_path = self.output_dir / entity_type / f'{entity_id}.json'
                with open(entity_path, 'w', encoding='utf-8') as f:
                    json.dump(entity_detail, f, ensure_ascii=False, separators=(',', ':'))

                total_files_size += entity_path.stat().st_size
                entities_with_locations += 1

        # Sort index entries by article count
        for entity_type in index_data:
            index_data[entity_type].sort(key=lambda x: x['articleCount'], reverse=True)

        # Save index file
        index_output = {
            'entities': index_data,
            'typeLabels': TYPE_LABELS,
            'metadata': {
                'totalEntities': len(self.entity_by_id),
                'entitiesWithLocations': entities_with_locations,
                'entityTypes': list(INCLUDED_ENTITY_TYPES),
                'generatedAt': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                'dataSource': DATASET_ID
            }
        }

        index_path = self.output_dir / 'index.json'
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_output, f, ensure_ascii=False, separators=(',', ':'))

        index_size = index_path.stat().st_size / 1024
        logger.info(f"Saved index to {index_path} ({index_size:.1f} KB)")
        logger.info(f"Generated {entities_with_locations} individual entity files")
        logger.info(f"Total entity files size: {total_files_size / (1024 * 1024):.2f} MB")

    def process(self) -> None:
        """Run the full data generation pipeline."""
        self.load_location_coordinates()
        self.fetch_index()
        self.fetch_articles()
        self.build_entity_lookup()
        self.process_articles()
        self.generate_output()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate entity spatial data from IWAC dataset'
    )
    parser.add_argument(
        '--output-dir',
        default='static/data',
        help='Output directory for JSON files (default: static/data)'
    )

    args = parser.parse_args()

    generator = EntitySpatialGenerator(output_dir=args.output_dir)
    generator.process()
    logger.info("Entity spatial data generation completed!")


if __name__ == "__main__":
    main()
