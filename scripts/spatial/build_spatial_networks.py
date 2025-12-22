#!/usr/bin/env python3
"""build_spatial_networks.py
Generate spatial network data with GPS coordinates for IWAC Spatial Overview.

This script creates network data specifically for locations with geographic coordinates,
enabling visualization on a Leaflet map with Sigma.js overlay.

INPUT: 
    - omeka-map-explorer/static/data/entities/locations.json (already has coordinates!)
    - omeka-map-explorer/static/data/articles.json

OUTPUT:
    - omeka-map-explorer/static/data/networks/spatial.json (location network with coordinates)

The output includes:
    - nodes: locations with GPS coordinates, article counts, and network metrics
    - edges: co-occurrence relationships between locations from shared articles
    - bounds: geographic bounds for map initialization
    - meta: generation metadata and statistics
"""

from __future__ import annotations
import json
import argparse
from pathlib import Path
from datetime import datetime
from statistics import fmean
from typing import Dict, List, Tuple, Optional

# ------------------ Configuration ------------------
DEFAULT_WEIGHT_MIN = 2

# ------------------ Paths ------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'omeka-map-explorer' / 'static' / 'data'
ENT_DIR = DATA_DIR / 'entities'
OUT_DIR = DATA_DIR / 'networks'
OUT_DIR.mkdir(parents=True, exist_ok=True)

def parse_args():
    parser = argparse.ArgumentParser(description="Build spatial network with GPS coordinates")
    parser.add_argument("--weight-min", type=int, default=DEFAULT_WEIGHT_MIN, 
                       help="Minimum edge weight to keep")
    return parser.parse_args()

def load_articles() -> List[Dict]:
    """Load articles data."""
    articles_file = DATA_DIR / 'articles.json'
    if not articles_file.exists():
        print(f"❌ Articles file not found: {articles_file}")
        return []
    
    print(f"📰 Loading articles from {articles_file}")
    return json.loads(articles_file.read_text(encoding='utf-8'))

def load_locations() -> List[Dict]:
    """Load locations data."""
    locations_file = ENT_DIR / 'locations.json'
    if not locations_file.exists():
        print(f"❌ Locations file not found: {locations_file}")
        return []
    
    print(f"📍 Loading locations from {locations_file}")
    return json.loads(locations_file.read_text(encoding='utf-8'))

def build_spatial_network(args):
    """Build the spatial network using existing coordinate data."""
    
    print("🚀 Building spatial network...")
    
    # Load data
    articles = load_articles()
    locations = load_locations()
    
    if not articles or not locations:
        print("❌ Missing required data files")
        return
    
    print(f"📊 Loaded {len(articles)} articles and {len(locations)} locations")
    
    # Build location nodes with coordinates (filter out locations without coordinates)
    nodes = []
    locations_with_coords = 0
    
    for location in locations:
        location_name = location.get('name', '').strip()
        coordinates = location.get('coordinates')
        
        if not location_name or not coordinates:
            continue
        
        # Validate coordinates format
        if not isinstance(coordinates, list) or len(coordinates) != 2:
            continue
        
        try:
            lat, lng = float(coordinates[0]), float(coordinates[1])
        except (ValueError, TypeError):
            continue
        
        # Skip invalid coordinates
        if abs(lat) > 90 or abs(lng) > 180:
            continue
        
        node = {
            'id': f"location:{location['id']}",
            'type': 'location',
            'label': location_name,
            'count': location.get('articleCount', len(location.get('relatedArticleIds', []))),
            'coordinates': [lat, lng],  # [lat, lng]
            'country': location.get('country', ''),
            'region': location.get('region', ''),
            'prefecture': location.get('prefecture', ''),
            'relatedArticleIds': location.get('relatedArticleIds', [])
        }
        
        nodes.append(node)
        locations_with_coords += 1
    
    print(f"📍 Found {locations_with_coords} locations with valid coordinates")
    
    # Build article index for co-occurrence calculation
    article_to_locations = {}
    node_by_name = {node['label'].lower(): node for node in nodes}
    
    for article in articles:
        article_id = str(article.get('o:id', ''))
        spatial = article.get('spatial', '')
        if not spatial:
            continue
        
        # Parse locations from spatial field and match to nodes with coordinates
        article_locations = []
        for loc_name in spatial.split('|'):
            loc_name = loc_name.strip()
            if not loc_name:
                continue
            
            # Find matching node by name
            node = node_by_name.get(loc_name.lower())
            if node:
                article_locations.append(node['id'])
        
        # Only articles with multiple locations create edges
        if len(article_locations) > 1:
            article_to_locations[article_id] = article_locations
    
    print(f"🔗 Found {len(article_to_locations)} articles with multiple coordinate-enabled locations")
    
    # Build edges (co-occurrence between locations)
    edge_weights = {}
    
    for article_id, location_ids in article_to_locations.items():
        # Create edges between all pairs of locations in this article
        for i, loc1 in enumerate(location_ids):
            for loc2 in location_ids[i + 1:]:
                edge_key = tuple(sorted([loc1, loc2]))
                
                if edge_key not in edge_weights:
                    edge_weights[edge_key] = {
                        'source': edge_key[0],
                        'target': edge_key[1],
                        'weight': 0,
                        'articleIds': []
                    }
                
                edge_weights[edge_key]['weight'] += 1
                edge_weights[edge_key]['articleIds'].append(article_id)
    
    # Filter edges by minimum weight
    edges = [
        edge for edge in edge_weights.values() 
        if edge['weight'] >= args.weight_min
    ]
    
    print(f"🔗 Created {len(edges)} edges (min weight: {args.weight_min})")
    
    # Calculate network metrics
    degree = {node['id']: 0 for node in nodes}
    strength = {node['id']: 0 for node in nodes}
    
    for edge in edges:
        degree[edge['source']] += 1
        degree[edge['target']] += 1
        strength[edge['source']] += edge['weight']
        strength[edge['target']] += edge['weight']
    
    # Add metrics to nodes
    for node in nodes:
        node['degree'] = degree[node['id']]
        node['strength'] = strength[node['id']]
    
    # Filter out isolated nodes (nodes with no edges)
    connected_node_ids = set()
    for edge in edges:
        connected_node_ids.add(edge['source'])
        connected_node_ids.add(edge['target'])
    
    nodes = [node for node in nodes if node['id'] in connected_node_ids]
    
    print(f"📊 Final network: {len(nodes)} connected nodes, {len(edges)} edges")
    
    # Calculate geographic bounds
    if nodes:
        lats = [node['coordinates'][0] for node in nodes]
        lngs = [node['coordinates'][1] for node in nodes]
        bounds = {
            'north': max(lats),
            'south': min(lats),
            'east': max(lngs),
            'west': min(lngs)
        }
        
        # Add padding
        lat_padding = (bounds['north'] - bounds['south']) * 0.1 or 0.1
        lng_padding = (bounds['east'] - bounds['west']) * 0.1 or 0.1
        bounds = {
            'north': bounds['north'] + lat_padding,
            'south': bounds['south'] - lat_padding,
            'east': bounds['east'] + lng_padding,
            'west': bounds['west'] - lng_padding
        }
    else:
        bounds = None
    
    # Add normalized edge weights
    if edges:
        max_weight = max(edge['weight'] for edge in edges)
        min_weight = min(edge['weight'] for edge in edges)
        for edge in edges:
            edge['weightNorm'] = edge['weight'] / max_weight if max_weight > 0 else 0
    
    # Prepare output
    output = {
        'nodes': nodes,
        'edges': edges,
        'bounds': bounds,
        'meta': {
            'generatedAt': datetime.utcnow().isoformat() + 'Z',
            'totalNodes': len(nodes),
            'totalEdges': len(edges),
            'weightMin': args.weight_min,
            'geocodedLocations': locations_with_coords,
            'totalLocationsInData': len(locations),
            'geocodingSuccessRate': round(locations_with_coords / len(locations) * 100, 1) if locations else 0,
            'bounds': bounds,
            'articlesWithMultipleLocations': len(article_to_locations)
        }
    }
    
    # Save output
    output_file = OUT_DIR / 'spatial.json'
    output_file.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    
    print(f"✅ Spatial network saved to {output_file}")
    print(f"📊 Statistics:")
    print(f"   - Nodes: {len(nodes)}")
    print(f"   - Edges: {len(edges)}")
    print(f"   - Locations with coordinates: {locations_with_coords}/{len(locations)} ({output['meta']['geocodingSuccessRate']}%)")
    if bounds:
        print(f"   - Geographic bounds: {bounds['south']:.2f}°S to {bounds['north']:.2f}°N, {bounds['west']:.2f}°W to {bounds['east']:.2f}°E")

if __name__ == "__main__":
    args = parse_args()
    build_spatial_network(args)
