---
description: Generate static JSON data files from Python scripts
---

# Generate Data

## Prerequisites

1. Install Python dependencies (one-time setup):
   ```bash
   cd scripts
   pip install -r requirements.txt
   cd ..
   ```

## Generate All Data

2. Run all data generation scripts:
   ```bash
   cd scripts
   python generate_overview_stats.py
   python generate_index_entities.py
   python generate_language_facets.py
   python generate_treemap.py
   python generate_wordcloud.py
   python generate_timeline.py
   python generate_categories.py
   python generate_scary_terms.py
   python generate_cooccurrence.py
   python generate_references.py
   python generate_sources.py
   python generate_world_map.py
   python generate_topic_explorer_data.py
   cd ..
   ```

## Individual Data Scripts

- `generate_overview_stats.py` - Overview dashboard statistics
- `generate_index_entities.py` - Entity index (persons, organizations, etc.)
- `generate_language_facets.py` - Language distribution data
- `generate_treemap.py` - Country treemap hierarchy
- `generate_wordcloud.py` - Word frequency data
- `generate_timeline.py` - Collection growth timeline
- `generate_categories.py` - Document type categories
- `generate_scary_terms.py` - "Scary" terminology analysis
- `generate_cooccurrence.py` - Term co-occurrence matrix
- `generate_references.py` - Bibliographic references
- `generate_sources.py` - Source/newspaper data
- `generate_world_map.py` - Geographic location data
- `generate_topic_explorer_data.py` - Topic modeling data

## Output

Generated JSON files are saved to:
- `static/data/` - For development
- `build/data/` - For production (if build exists)
