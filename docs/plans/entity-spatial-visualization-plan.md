# Entity Spatial Visualization Plan

## Overview

Create an interactive visualization that displays the geographic footprint of index entities (persons, events, subjects, organisations) on a map, showing all locations where articles mention that entity.

## User Requirements

1. **Category Selector**: Choose entity type (Persons, Events, Topics, Organizations)
2. **Entity Picker**: Searchable dropdown/combobox to select a specific entity
3. **Summary Cards**: Display article count, countries covered, time period
4. **Interactive Map**: Show all locations associated with the selected entity
5. **Location Click**: Open panel listing articles/publications at that location mentioning the entity

## Data Architecture Challenge

### Current Data Limitations

The existing `index-entities.json` has:
```json
{
  "o:id": 123,
  "Titre": "Boukary Savadogo",
  "Type": "Personnes",
  "frequency": 45,
  "first_occurrence": "2010-01-15",
  "last_occurrence": "2023-06-20",
  "countries": "Burkina Faso | Niger"
}
```

**Problem**: No direct link from entities → locations → articles

**Solution**: Create a new Python script to pre-compute the entity-location-article mapping

### Proposed Data Structure

Create `static/data/entity-spatial.json` with two parts:

#### 1. Entity Index (for picker/search)
```json
{
  "entities": {
    "Personnes": [
      { "id": 123, "name": "Boukary Savadogo", "articleCount": 45, "locationCount": 8 },
      ...
    ],
    "Événements": [...],
    "Sujets": [...],
    "Organisations": [...]
  }
}
```

#### 2. Entity Details (lazy-loaded per entity or bundled)
```json
{
  "entityDetails": {
    "123": {
      "id": 123,
      "name": "Boukary Savadogo",
      "type": "Personnes",
      "stats": {
        "articleCount": 45,
        "countries": ["Burkina Faso", "Niger"],
        "dateRange": { "first": "2010-01-15", "last": "2023-06-20" }
      },
      "locations": [
        {
          "name": "Ouagadougou",
          "lat": 12.3714,
          "lng": -1.5197,
          "country": "Burkina Faso",
          "articleCount": 28,
          "articles": [
            { "id": "2233", "title": "Formation des imams...", "date": "2018-04-05", "type": "article", "newspaper": "Le Pays" },
            ...
          ]
        },
        ...
      ]
    }
  }
}
```

### Data Size Considerations

- ~4,700 entities total
- User wants 4 categories: ~3,700 entities (excluding Locations & Authority Files)
- Each entity may link to 0-100+ locations
- Each location may have 1-50+ articles

**Strategy for Static Site Performance**:

**Option A: Single Bundled File** (simpler, works for moderate data)
- Generate one JSON file with all entity details
- Estimate: 5-15 MB depending on article detail level
- Pros: Single fetch, simple caching
- Cons: Large initial download

**Option B: Split Files** (better for large datasets)
- `entity-spatial-index.json`: Entity list for picker (~100 KB)
- `entity-spatial/{entityId}.json`: Individual entity details (~1-20 KB each)
- Pros: Load only what's needed
- Cons: Multiple network requests

**Recommendation**: Start with **Option A** for simplicity. If file size exceeds 5 MB, switch to Option B with lazy loading.

## Implementation Plan

### Phase 1: Data Generation Script

**File**: `scripts/generate_entity_spatial.py`

**Steps**:
1. Load `articles` and `index` subsets from Hugging Face
2. Build entity lookup from index (filtering to 4 types)
3. Parse `subject` field in articles to find entity mentions
4. Extract `spatial` field and match to location coordinates
5. Aggregate articles by entity → location
6. Output structured JSON

**Key Logic**:
```python
# Pseudocode
for article in articles:
    subjects = parse_pipe_separated(article['subject'])
    locations = parse_pipe_separated(article['spatial'])

    for subject in subjects:
        entity = find_entity_by_name(subject)
        if entity and entity.type in ALLOWED_TYPES:
            for location in locations:
                coords = get_coordinates(location)
                entity_spatial[entity.id].locations[location].articles.append(article)
```

**Coordinate Source**:
- Use existing `static/data/world-map.json` for location coordinates
- Or extract from index "Lieux" entries if they have coordinates

### Phase 2: Svelte Components

#### 2.1 New Route: `src/routes/entity-spatial/`

**Files**:
- `+page.ts` - Data loader with prerender
- `+page.svelte` - Main page component

#### 2.2 New Components

**EntityCategorySelector.svelte**
- Radio group or tabs for 4 categories
- Uses shadcn-svelte RadioGroup or Tabs
- Bilingual labels via translation store

**EntityPicker.svelte**
- Combobox with search functionality
- Uses shadcn-svelte Combobox component
- Filters entity list as user types
- Shows entity name + article count

**EntityStatsCards.svelte**
- Three cards in a row: Articles, Countries, Time Period
- Uses shadcn-svelte Card component
- Animated number transitions (optional)

**EntityLocationMap.svelte**
- Leaflet map centered on West Africa
- Bubble markers sized by article count
- Click handler to select location
- Uses existing Map component as base

**LocationArticlePanel.svelte**
- Slide-in panel or modal
- Lists articles at selected location
- Shows: title, date, newspaper, type
- Link to external Omeka record

### Phase 3: State Management

**Create**: `src/lib/stores/entitySpatialStore.svelte.ts`

```typescript
class EntitySpatialStore {
  // State
  selectedCategory = $state<string>('Personnes');
  selectedEntityId = $state<number | null>(null);
  selectedLocation = $state<string | null>(null);

  // Data
  entityIndex = $state<EntityIndex | null>(null);
  entityDetails = $state<Record<number, EntityDetail>>({});

  // Derived
  entitiesInCategory = $derived(() => ...);
  currentEntity = $derived(() => ...);
  currentLocationArticles = $derived(() => ...);
}
```

### Phase 4: Integration

1. Add navigation link to sidebar
2. Add translation keys for all UI text
3. Test language switching
4. Test responsiveness

## File Structure

```
scripts/
  generate_entity_spatial.py    # NEW: Data generator

static/data/
  entity-spatial.json           # NEW: Generated data

src/lib/
  stores/
    entitySpatialStore.svelte.ts  # NEW: State management

  components/
    visualizations/
      entity-spatial/             # NEW: Component folder
        index.ts
        EntityCategorySelector.svelte
        EntityPicker.svelte
        EntityStatsCards.svelte
        EntityLocationMap.svelte
        LocationArticlePanel.svelte

src/routes/
  entity-spatial/               # NEW: Route
    +page.ts
    +page.svelte
```

## Translation Keys to Add

```typescript
// English
'entity_spatial.title': 'Entity Geographic Footprint',
'entity_spatial.description': 'Explore where index entities appear across West Africa',
'entity_spatial.select_category': 'Select Category',
'entity_spatial.search_entity': 'Search for an entity...',
'entity_spatial.no_entity_selected': 'Select an entity to view its geographic footprint',
'entity_spatial.articles_count': 'Articles',
'entity_spatial.countries_count': 'Countries',
'entity_spatial.time_period': 'Time Period',
'entity_spatial.location_panel_title': 'Articles in {0}',
'entity_spatial.view_article': 'View Article',

// French
'entity_spatial.title': 'Empreinte Géographique des Entités',
'entity_spatial.description': 'Explorez où les entités apparaissent en Afrique de l\'Ouest',
'entity_spatial.select_category': 'Sélectionner une Catégorie',
'entity_spatial.search_entity': 'Rechercher une entité...',
'entity_spatial.no_entity_selected': 'Sélectionnez une entité pour voir son empreinte géographique',
'entity_spatial.articles_count': 'Articles',
'entity_spatial.countries_count': 'Pays',
'entity_spatial.time_period': 'Période',
'entity_spatial.location_panel_title': 'Articles à {0}',
'entity_spatial.view_article': 'Voir l\'Article',
```

## Technical Considerations

### 1. Entity Name Matching

The `subject` field in articles contains entity names (not IDs). Matching strategy:
- Normalize both sides: lowercase, remove accents, trim whitespace
- Build a name → entity ID lookup from index
- Handle partial matches carefully (avoid false positives)

### 2. Location Coordinates

Need lat/lng for each location. Sources:
- Existing `world-map.json` has coordinates for many locations
- Index "Lieux" entries may have `Coordonnées` field
- Fall back to country centroid if specific location not found

### 3. Performance Optimizations

- Use `$derived` with memoization for filtered lists
- Virtual scrolling for entity picker if >500 items
- Debounce search input
- Lazy load entity details if using split files

### 4. Map Interaction

- Cluster nearby markers when zoomed out
- Use different colors per country
- Tooltip on hover showing location name + count
- Click to open article panel

## Development Steps

### Step 1: Python Data Generator
- [ ] Create `generate_entity_spatial.py`
- [ ] Load and process articles + index datasets
- [ ] Build entity-location-article mapping
- [ ] Add coordinate lookup
- [ ] Output JSON with proper structure
- [ ] Test with sample entities

### Step 2: Store and Types
- [ ] Define TypeScript interfaces
- [ ] Create `entitySpatialStore.svelte.ts`
- [ ] Implement category filtering
- [ ] Implement entity selection

### Step 3: UI Components
- [ ] EntityCategorySelector (tabs/radio)
- [ ] EntityPicker (combobox with search)
- [ ] EntityStatsCards (3 stat cards)
- [ ] EntityLocationMap (Leaflet markers)
- [ ] LocationArticlePanel (article list)

### Step 4: Page Route
- [ ] Create route with data loader
- [ ] Compose components
- [ ] Wire up interactions

### Step 5: Polish
- [ ] Add translations (EN/FR)
- [ ] Add to sidebar navigation
- [ ] Test responsiveness
- [ ] Test language switching
- [ ] Verify prerender works

## Dependencies

**Existing** (no new packages needed):
- Leaflet (maps)
- shadcn-svelte (UI components)
- LayerChart (potential for stats visualization)

**Python** (existing):
- datasets (Hugging Face)
- pandas
- shapely (for coordinate operations)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large JSON file | Slow load | Split files, lazy loading |
| Entity name mismatch | Missing data | Fuzzy matching, logging unmatched |
| Missing coordinates | Incomplete map | Use country centroid fallback |
| Too many markers | Cluttered map | Marker clustering, limit per entity |

## Success Criteria

1. User can select entity category from 4 options
2. User can search and select any entity in that category
3. Summary cards update with correct statistics
4. Map shows all locations with correct marker sizes
5. Clicking location shows article list panel
6. Articles link to external Omeka database
7. All text is bilingual (EN/FR)
8. Page prerenders correctly for static deployment
