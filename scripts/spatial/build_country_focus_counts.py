#!/usr/bin/env python3
"""
Build precomputed per-admin counts for Country Focus (FAST + ACCURATE).

Reads location entities data from:
- omeka-map-explorer/static/data/entities/locations.json

This provides accurate article counts per location since the entities file
contains the actual relationships between locations and articles, unlike
index.json which only contains raw location mentions.

What this script does:
- For the four focus countries, aggregate article counts per Region and per Prefecture from location entities.
- Use the articleCount field from each location entity for accurate totals.
- Write compact JSONs to static/data/country_focus/ matching frontend loader naming.

Outputs (to omeka-map-explorer/static/data/country_focus/):
- benin_regions_counts.json
- benin_prefectures_counts.json
- burkina_faso_regions_counts.json
- burkina_faso_prefectures_counts.json
- cote_divoire_regions_counts.json
- cote_divoire_prefectures_counts.json
- togo_regions_counts.json
- togo_prefectures_counts.json
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'omeka-map-explorer' / 'static' / 'data'
OUT_DIR = DATA_DIR / 'country_focus'
OUT_DIR.mkdir(parents=True, exist_ok=True)

COUNTRIES = ['Benin', 'Burkina Faso', "Côte d'Ivoire", 'Togo']


def norm_country_for_file(name: str) -> str:
    s = unicodedata.normalize('NFD', name)
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')  # strip diacritics
    s = s.replace("'", '').replace('’', '').replace('`', '')
    s = '_'.join(s.split()).lower()
    return s


def load_json(path: Path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # Load location entities which have the accurate article counts
    locations_data = load_json(DATA_DIR / 'entities' / 'locations.json')

    # Prepare counters:
    # - articles: count from relatedArticleIds
    # - mentions: use articleCount from entities (more accurate)
    reg_articles = {c: defaultdict(int) for c in COUNTRIES}  # name -> article count
    pre_articles = {c: defaultdict(int) for c in COUNTRIES}
    reg_mentions = {c: defaultdict(int) for c in COUNTRIES}  # name -> article count (same as articles for entities)
    pre_mentions = {c: defaultdict(int) for c in COUNTRIES}

    for location in locations_data:
        country = location.get('country', '')
        if country not in COUNTRIES:
            continue
        
        region = location.get('region', '')
        prefecture = location.get('prefecture', '')
        article_count = location.get('articleCount', 0)
        
        if region:
            reg_articles[country][region] += article_count
            reg_mentions[country][region] += article_count
        if prefecture:
            pre_articles[country][prefecture] += article_count
            pre_mentions[country][prefecture] += article_count

    now = datetime.utcnow().isoformat()
    for country in COUNTRIES:
        norm = norm_country_for_file(country)
        reg_out = {
            'country': country,
            'level': 'regions',
            'countsMentions': {k: v for k, v in sorted(reg_mentions[country].items())},
            'countsArticles': {k: v for k, v in sorted(reg_articles[country].items())},
            'updatedAt': now,
        }
        pre_out = {
            'country': country,
            'level': 'prefectures',
            'countsMentions': {k: v for k, v in sorted(pre_mentions[country].items())},
            'countsArticles': {k: v for k, v in sorted(pre_articles[country].items())},
            'updatedAt': now,
        }
        with (OUT_DIR / f"{norm}_regions_counts.json").open('w', encoding='utf-8') as f:
            json.dump(reg_out, f, ensure_ascii=False, indent=2)
        with (OUT_DIR / f"{norm}_prefectures_counts.json").open('w', encoding='utf-8') as f:
            json.dump(pre_out, f, ensure_ascii=False, indent=2)

    print(f"Wrote precomputed counts to {OUT_DIR}")


if __name__ == '__main__':
    main()
