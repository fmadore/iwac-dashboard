#!/usr/bin/env python3
"""
Simplify world_countries.geojson by reducing coordinate precision
and removing unnecessary properties.
"""

import json
from pathlib import Path

def simplify_coords(coords, precision=2):
    """Recursively round coordinates to given precision."""
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], precision), round(coords[1], precision)]
    return [simplify_coords(c, precision) for c in coords]

def remove_duplicate_consecutive(coords):
    """Remove consecutive duplicate coordinates."""
    if not coords or isinstance(coords[0], (int, float)):
        return coords

    if isinstance(coords[0][0], (int, float)):
        # This is a ring of coordinates
        result = [coords[0]]
        for c in coords[1:]:
            if c != result[-1]:
                result.append(c)
        return result

    # Nested structure
    return [remove_duplicate_consecutive(c) for c in coords]

def simplify_geometry(geometry, precision=2):
    """Simplify geometry coordinates."""
    if geometry is None:
        return None

    geom_type = geometry.get('type')
    coords = geometry.get('coordinates')

    if coords is None:
        return geometry

    # Simplify coordinates
    simplified = simplify_coords(coords, precision)
    # Remove duplicates
    simplified = remove_duplicate_consecutive(simplified)

    return {
        'type': geom_type,
        'coordinates': simplified
    }

def main():
    input_path = Path(__file__).parent.parent / 'static' / 'data' / 'maps' / 'world_countries.geojson'
    output_path = Path(__file__).parent.parent / 'static' / 'data' / 'maps' / 'world_countries_simple.geojson'

    print(f"Reading {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Original features: {len(data['features'])}")

    # Simplify each feature
    simplified_features = []
    for feature in data['features']:
        props = feature.get('properties', {})
        # Keep only essential properties
        simple_props = {
            'name': props.get('name') or props.get('NAME') or props.get('ADMIN', 'Unknown')
        }

        simplified_features.append({
            'type': 'Feature',
            'properties': simple_props,
            'geometry': simplify_geometry(feature.get('geometry'), precision=1)
        })

    output = {
        'type': 'FeatureCollection',
        'features': simplified_features
    }

    print(f"Writing {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, separators=(',', ':'))

    # Compare sizes
    orig_size = input_path.stat().st_size / 1024 / 1024
    new_size = output_path.stat().st_size / 1024 / 1024
    print(f"Original: {orig_size:.2f} MB")
    print(f"Simplified: {new_size:.2f} MB")
    print(f"Reduction: {(1 - new_size/orig_size) * 100:.1f}%")

if __name__ == '__main__':
    main()
