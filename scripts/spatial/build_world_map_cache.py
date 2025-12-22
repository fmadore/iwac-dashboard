#!/usr/bin/env python3
"""
Build precomputed world map cache for FAST rendering.

This script creates optimized JSON files to eliminate real-time calculations
that slow down the world map view. It generates:

1. Choropleth data: Country-level article counts for different views
2. Coordinate clusters: Pre-aggregated location data for map markers
3. Filtered datasets: Common filter combinations pre-computed

Outputs to omeka-map-explorer/static/data/world_cache/:
- choropleth/all_countries.json          # Global country counts
- choropleth/by_year/*.json              # Per-year country counts  
- choropleth/by_entity/*.json            # Per-entity-type country counts
- coordinates/all_locations.json         # Pre-aggregated coordinate clusters
- coordinates/by_country/*.json          # Country-specific coordinates
- metadata.json                          # Cache info and timestamps

Uses the same accurate entity-based data source as country focus.
"""

from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import unicodedata
from typing import Dict, List, Set, Any, Optional

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'omeka-map-explorer' / 'static' / 'data'
CACHE_DIR = DATA_DIR / 'world_cache'

# Create cache directories
(CACHE_DIR / 'choropleth').mkdir(parents=True, exist_ok=True)
(CACHE_DIR / 'choropleth' / 'by_year').mkdir(parents=True, exist_ok=True)
(CACHE_DIR / 'choropleth' / 'by_entity').mkdir(parents=True, exist_ok=True)
(CACHE_DIR / 'choropleth' / 'by_article_country').mkdir(parents=True, exist_ok=True)
(CACHE_DIR / 'coordinates').mkdir(parents=True, exist_ok=True)
(CACHE_DIR / 'coordinates' / 'by_country').mkdir(parents=True, exist_ok=True)
(CACHE_DIR / 'coordinates' / 'by_article_country').mkdir(parents=True, exist_ok=True)

def load_json(path: Path):
    """Load JSON file with error handling."""
    try:
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return None

def save_json(path: Path, data: Any, compact: bool = False):
    """Save JSON file, optionally compact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f:
        if compact:
            json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)

def normalize_country_filename(country: str) -> str:
    """Normalize country name for filenames."""
    s = unicodedata.normalize('NFD', country)
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    s = s.replace("'", '').replace("'", '').replace('`', '').replace(' ', '_')
    return s.lower()

def extract_year(date_str: str) -> Optional[int]:
    """Extract year from date string."""
    if not date_str:
        return None
    try:
        # Handle YYYY-MM-DD format
        if '-' in date_str:
            return int(date_str.split('-')[0])
        # Handle YYYY format
        return int(date_str)
    except (ValueError, IndexError):
        return None

def build_choropleth_cache():
    """Build choropleth data cache for fast country coloring."""
    print("Building choropleth cache...")
    
    # Load source data - use articles.json directly for accurate counts
    articles_data = load_json(DATA_DIR / 'articles.json')
    locations_data = load_json(DATA_DIR / 'entities' / 'locations.json')
    
    if not articles_data:
        print("Error: Could not load articles.json")
        return
    
    # Create location-to-country mapping from location entities
    location_to_country = {}
    if locations_data:
        for location in locations_data:
            name = location.get('name', '').strip()
            country = location.get('country', '').strip()
            if name and country:
                location_to_country[name] = country
    
    # Build country counts directly from articles (one count per article per country)
    country_counts = defaultdict(int)
    country_counts_by_year = defaultdict(lambda: defaultdict(int))
    
    # Track unique article-country pairs to avoid double counting
    processed_articles = 0
    
    for article in articles_data:
        article_id = str(article.get('o:id', ''))
        if not article_id:
            continue
            
        processed_articles += 1
        
        # Get countries this article should count for
        countries_for_article = set()
        
        # 1. Direct country field
        direct_country = article.get('country', '').strip()
        if direct_country:
            countries_for_article.add(direct_country)
        
        # 2. Countries from spatial locations
        spatial = article.get('spatial', '')
        if spatial:
            spatial_places = [place.strip() for place in spatial.split('|') if place.strip()]
            for place in spatial_places:
                # Check if this place is a known country name
                if place in ['Bénin', 'Benin', 'Burkina Faso', 'Côte d\'Ivoire', 'Togo', 'Niger', 'Nigéria', 'Nigeria', 'Cameroun', 'Cameroon', 'Tchad', 'Chad']:
                    # Normalize country names
                    normalized_country = place
                    if place in ['Bénin']: normalized_country = 'Benin'
                    elif place in ['Nigéria']: normalized_country = 'Nigeria'
                    elif place in ['Cameroun']: normalized_country = 'Cameroon'
                    elif place in ['Tchad']: normalized_country = 'Chad'
                    countries_for_article.add(normalized_country)
                elif place in location_to_country:
                    # Look up country for this location
                    countries_for_article.add(location_to_country[place])
        
        # Count this article once for each country it mentions
        for country in countries_for_article:
            country_counts[country] += 1
            
            # Year-based counts
            year = extract_year(article.get('pub_date', ''))
            if year:
                country_counts_by_year[year][country] += 1
    
    print(f"  Processed {processed_articles} articles")
    
    # Save global country counts
    global_data = {
        'type': 'global_choropleth',
        'counts': dict(country_counts),
        'total_articles': sum(country_counts.values()),
        'total_countries': len(country_counts),
        'unique_articles_processed': processed_articles,
        'updatedAt': datetime.utcnow().isoformat()
    }
    save_json(CACHE_DIR / 'choropleth' / 'all_countries.json', global_data, compact=True)
    print(f"  Saved global choropleth: {len(country_counts)} countries, {sum(country_counts.values())} article-country pairs from {processed_articles} unique articles")
    
    # Save year-based counts
    for year, year_counts in country_counts_by_year.items():
        if year and len(year_counts) > 0:
            year_data = {
                'type': 'yearly_choropleth',
                'year': year,
                'counts': dict(year_counts),
                'total_articles': sum(year_counts.values()),
                'total_countries': len(year_counts),
                'updatedAt': datetime.utcnow().isoformat()
            }
            save_json(CACHE_DIR / 'choropleth' / 'by_year' / f'{year}.json', year_data, compact=True)
    
    print(f"  Saved yearly choropleth: {len(country_counts_by_year)} years")

def build_entity_choropleth_cache():
    """Build entity-specific choropleth cache."""
    print("Building entity choropleth cache...")
    
    # Load entity data
    entity_types = ['persons', 'organizations', 'events', 'subjects']
    articles_data = load_json(DATA_DIR / 'articles.json')
    
    if not articles_data:
        print("Error: Could not load articles data")
        return
        
    articles_by_id = {str(article['o:id']): article for article in articles_data}
    
    for entity_type in entity_types:
        entity_file = DATA_DIR / 'entities' / f'{entity_type}.json'
        entities_data = load_json(entity_file)
        
        if not entities_data:
            print(f"  Skipping {entity_type}: file not found")
            continue
            
        # Collect all articles that mention any entity of this type
        entity_article_ids = set()
        for entity in entities_data:
            related_articles = entity.get('relatedArticleIds', [])
            entity_article_ids.update(str(aid) for aid in related_articles)
        
        # Count countries for these articles
        country_counts = defaultdict(int)
        locations_data = load_json(DATA_DIR / 'entities' / 'locations.json')
        
        if locations_data:
            article_country_pairs = set()
            for location in locations_data:
                country = location.get('country', '').strip()
                if not country:
                    continue
                    
                related_articles = location.get('relatedArticleIds', [])
                for article_id in related_articles:
                    article_id_str = str(article_id)
                    
                    # Only count if this article mentions the entity type
                    if article_id_str not in entity_article_ids:
                        continue
                        
                    pair_key = f"{article_id_str}:{country}"
                    if pair_key in article_country_pairs:
                        continue
                    article_country_pairs.add(pair_key)
                    
                    country_counts[country] += 1
        
        # Save entity choropleth data
        entity_data = {
            'type': 'entity_choropleth',
            'entity_type': entity_type,
            'counts': dict(country_counts),
            'total_articles': sum(country_counts.values()),
            'total_countries': len(country_counts),
            'updatedAt': datetime.utcnow().isoformat()
        }
        save_json(CACHE_DIR / 'choropleth' / 'by_entity' / f'{entity_type}.json', entity_data, compact=True)
        print(f"  Saved {entity_type} choropleth: {len(country_counts)} countries, {sum(country_counts.values())} articles")

def build_coordinates_cache():
    """Build coordinate cluster cache for fast map marker rendering."""
    print("Building coordinates cache...")
    
    # Load location entities
    locations_data = load_json(DATA_DIR / 'entities' / 'locations.json')
    if not locations_data:
        print("Error: Could not load locations data")
        return
    
    # Aggregate coordinates by location clusters
    coordinate_clusters = []
    coordinates_by_country = defaultdict(list)
    
    for location in locations_data:
        coords = location.get('coordinates')
        if not coords or not isinstance(coords, list) or len(coords) != 2:
            continue
            
        try:
            # Parse coordinates (already in [lat, lng] format)
            lat, lng = float(coords[0]), float(coords[1])
            
            # Validate coordinates
            if lat < -90 or lat > 90 or lng < -180 or lng > 180:
                continue
                
            country = location.get('country', '').strip()
            region = location.get('region', '').strip()
            prefecture = location.get('prefecture', '').strip()
            
            cluster = {
                'id': location.get('id'),
                'label': location.get('name', ''),  # Use 'name' field for label
                'coordinates': [lat, lng],
                'country': country,
                'region': region,
                'prefecture': prefecture,
                'articleCount': location.get('articleCount', 0),
                'relatedArticleIds': location.get('relatedArticleIds', [])
            }
            
            coordinate_clusters.append(cluster)
            
            # Group by country for country-specific caches
            if country:
                coordinates_by_country[country].append(cluster)
                
        except (ValueError, TypeError, AttributeError):
            continue
    
    # Save global coordinate clusters
    global_coords_data = {
        'type': 'coordinate_clusters',
        'clusters': coordinate_clusters,
        'total_clusters': len(coordinate_clusters),
        'total_articles': sum(c['articleCount'] for c in coordinate_clusters),
        'updatedAt': datetime.utcnow().isoformat()
    }
    save_json(CACHE_DIR / 'coordinates' / 'all_locations.json', global_coords_data, compact=True)
    print(f"  Saved global coordinates: {len(coordinate_clusters)} clusters")
    
    # Save country-specific coordinate clusters
    for country, clusters in coordinates_by_country.items():
        if len(clusters) > 0:
            country_coords_data = {
                'type': 'country_coordinates',
                'country': country,
                'clusters': clusters,
                'total_clusters': len(clusters),
                'total_articles': sum(c['articleCount'] for c in clusters),
                'updatedAt': datetime.utcnow().isoformat()
            }
            filename = normalize_country_filename(country)
            save_json(CACHE_DIR / 'coordinates' / 'by_country' / f'{filename}.json', country_coords_data, compact=True)
    
    print(f"  Saved country coordinates: {len(coordinates_by_country)} countries")

def build_article_country_coordinates_cache():
    """Build coordinate clusters grouped by ARTICLE country (articleCountry).

    Semantics: For each articleCountry (country field in articles.json), include ALL location
    coordinates referenced by any article with that articleCountry, regardless of the location's
    own country. This powers fast multi-country union selection on the client.
    """
    print("Building article-country coordinate cache (union semantics)...")
    articles = load_json(DATA_DIR / 'articles.json')
    locations = load_json(DATA_DIR / 'entities' / 'locations.json')
    if not articles or not locations:
        print("  Skipping article-country cache (missing articles or locations)")
        return

    # Map article id -> article country
    article_country: Dict[str, str] = {}
    for a in articles:
        aid = str(a.get('o:id', '')).strip()
        if not aid:
            continue
        c = (a.get('country', '') or '').strip()
        if c:
            article_country[aid] = c

    # articleCountry -> coordKey -> {lat, lng, articleIds:Set[str], names:Set[str]}
    from collections import defaultdict
    per_ac: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)

    def coord_key(lat: float, lng: float) -> str:
        return f"{lat:.4f},{lng:.4f}"

    for loc in locations:
        coords = loc.get('coordinates')
        if not coords or not isinstance(coords, list) or len(coords) != 2:
            continue
        try:
            lat, lng = float(coords[0]), float(coords[1])
        except (ValueError, TypeError):
            continue
        if lat < -90 or lat > 90 or lng < -180 or lng > 180:
            continue
        related = loc.get('relatedArticleIds', []) or []
        name = (loc.get('name') or '').strip()
        for ra in related:
            ra_id = str(ra)
            ac = article_country.get(ra_id)
            if not ac:
                continue
            bucket = per_ac[ac]
            k = coord_key(lat, lng)
            entry = bucket.get(k)
            if not entry:
                entry = {'lat': lat, 'lng': lng, 'articleIds': set(), 'names': set()}
                bucket[k] = entry
            entry['articleIds'].add(ra_id)
            if name:
                entry['names'].add(name)

    total_files = 0
    for ac, bucket in per_ac.items():
        clusters = []
        for k, entry in bucket.items():
            clusters.append({
                'id': k.replace(',', '_'),
                'label': sorted(entry['names'])[0] if entry['names'] else k,
                'coordinates': [entry['lat'], entry['lng']],
                'country': 'MIXED',  # location country not relevant for union semantics
                'region': '',
                'prefecture': '',
                'articleCount': len(entry['articleIds']),
                'relatedArticleIds': sorted(entry['articleIds'])
            })
        filename = normalize_country_filename(ac)
        out = {
            'type': 'article_country_coordinates',
            'articleCountry': ac,
            'clusters': clusters,
            'total_clusters': len(clusters),
            'total_articles': sum(c['articleCount'] for c in clusters),
            'updatedAt': datetime.utcnow().isoformat()
        }
        save_json(CACHE_DIR / 'coordinates' / 'by_article_country' / f'{filename}.json', out, compact=True)
    print(f"  Saved article-country coordinate clusters: {len(per_ac)} countries")

def build_article_country_choropleth_cache():
    """Build choropleth data BY article country for fast union operations.
    
    For each articleCountry (e.g., "Benin"), compute what location countries 
    its articles mention, with proper deduplication:
    - If one article mentions Cotonou + Porto-Novo + Baghdad, count as Benin: 1, Iraq: 1
    - NOT Benin: 2, Iraq: 1 (avoid double-counting same country per article)
    """
    print("Building article-country choropleth cache...")
    
    articles_data = load_json(DATA_DIR / 'articles.json')
    locations_data = load_json(DATA_DIR / 'entities' / 'locations.json')
    
    if not articles_data or not locations_data:
        print("  Skipping article-country choropleth cache (missing data)")
        return
        
    # Build article_id -> articleCountry mapping
    article_to_country = {}
    for article in articles_data:
        article_id = str(article.get('o:id', ''))
        if not article_id:
            continue
        article_country = (article.get('country', '') or '').strip()
        if article_country:
            article_to_country[article_id] = article_country
    
    # Build location_id -> country mapping  
    location_to_country = {}
    for location in locations_data:
        loc_id = str(location.get('id', ''))
        country = (location.get('country', '') or '').strip()
        if loc_id and country:
            location_to_country[loc_id] = country
    
    # Group by articleCountry: articleCountry -> {locationCountry -> set(unique_article_ids)}
    article_country_to_location_counts = defaultdict(lambda: defaultdict(set))
    
    # Process each location to find which articles mention it
    for location in locations_data:
        location_country = (location.get('country', '') or '').strip()
        if not location_country:
            continue
            
        related_articles = location.get('relatedArticleIds', []) or []
        for article_id in related_articles:
            article_id_str = str(article_id)
            article_country = article_to_country.get(article_id_str)
            if not article_country:
                continue
                
            # Add this article to the set for this article_country -> location_country pair
            # Using set ensures each article is counted only once per country pair
            article_country_to_location_counts[article_country][location_country].add(article_id_str)
    
    # Convert sets to counts and save cache files
    for article_country, location_data in article_country_to_location_counts.items():
        choropleth_counts = {}
        total_unique_articles = set()
        
        for location_country, article_ids_set in location_data.items():
            # Count = number of unique articles from this articleCountry that mention this locationCountry
            choropleth_counts[location_country] = len(article_ids_set)
            total_unique_articles.update(article_ids_set)
        
        # Save to cache file
        filename = normalize_country_filename(article_country)
        cache_data = {
            'type': 'article_country_choropleth',
            'articleCountry': article_country,
            'counts': choropleth_counts,
            'total_location_countries': len(choropleth_counts),
            'total_unique_articles': len(total_unique_articles),
            'updatedAt': datetime.utcnow().isoformat()
        }
        
        save_json(CACHE_DIR / 'choropleth' / 'by_article_country' / f'{filename}.json', cache_data, compact=True)
    
    print(f"  Saved article-country choropleth cache: {len(article_country_to_location_counts)} countries")

def build_metadata():
    """Rebuild metadata file after generating caches."""
    metadata = {
        'cache_version': '1.1',
        'generated_at': datetime.utcnow().isoformat(),
        'generator': 'build_world_map_cache.py',
        'description': 'Precomputed world map data for fast rendering',
        'structure': {
            'choropleth': {
                'all_countries.json': 'Global country counts for choropleth coloring',
                'by_year/': 'Yearly country counts',
                'by_entity/': 'Entity-type specific country counts',
                'by_article_country/': 'Article-country specific choropleth data with deduplication'
            },
            'coordinates': {
                'all_locations.json': 'Pre-aggregated coordinate clusters for markers',
                'by_country/': 'Country-specific coordinate clusters',
                'by_article_country/': 'Coordinate clusters grouped by article country (union semantics)'
            }
        },
        'usage': {
            'choropleth': 'Load appropriate file based on current filters to color world map',
            'coordinates': 'Load clusters to render map markers without real-time aggregation'
        }
    }
    save_json(CACHE_DIR / 'metadata.json', metadata, compact=False)
    print("  Saved cache metadata (v1.1)")

def main():
    """Main execution function."""
    print(f"Building world map cache in {CACHE_DIR}")
    print("=" * 50)
    
    # Build all cache components
    build_choropleth_cache()
    build_entity_choropleth_cache() 
    build_coordinates_cache()
    build_article_country_coordinates_cache()
    build_article_country_choropleth_cache()
    build_metadata()
    
    print("=" * 50)
    print(f"World map cache build complete!")
    print(f"Cache location: {CACHE_DIR}")
    
    # Show cache size summary
    cache_files = list(CACHE_DIR.rglob('*.json'))
    total_size = sum(f.stat().st_size for f in cache_files)
    print(f"Generated {len(cache_files)} cache files ({total_size / 1024:.1f} KB total)")

if __name__ == '__main__':
    main()
