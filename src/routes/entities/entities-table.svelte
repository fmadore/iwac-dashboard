<script lang="ts">
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
  import { DataTable } from '$lib/components/ui/data-table/index.js';
  import type { ColumnDef } from '$lib/components/ui/data-table/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
  import FilterIcon from '@lucide/svelte/icons/filter';
  import XIcon from '@lucide/svelte/icons/x';

  type EntityRow = {
    'o:id': number | null;
    Titre: string | null;
    Type: string | null;
    frequency: number;
    first_occurrence: string | null;
    last_occurrence: string | null;
    countries: string;
  };

  let rows = $state<EntityRow[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);
  
  // Facet state
  let selectedTypes = $state<Set<string>>(new Set());
  let selectedCountries = $state<Set<string>>(new Set());

  const enBase = 'https://islam.zmo.de/s/westafrica/item/';
  const frBase = 'https://islam.zmo.de/s/afrique_ouest/item/';
  const itemBase = $derived(languageStore.current === 'fr' ? frBase : enBase);

  // Get unique types and countries from data
  const availableTypes = $derived(
    [...new Set(rows.map(r => r.Type).filter(Boolean))].sort() as string[]
  );

  const availableCountries = $derived.by(() => {
    const countriesSet = new Set<string>();
    rows.forEach(r => {
      if (r.countries) {
        // Split by pipe (|) and trim whitespace
        r.countries.split('|').forEach(c => {
          const trimmed = c.trim();
          if (trimmed) countriesSet.add(trimmed);
        });
      }
    });
    return [...countriesSet].sort();
  });

  // Filter data based on selected facets
  const filteredRows = $derived.by(() => {
    let filtered = rows;
    
    // Filter by type
    if (selectedTypes.size > 0) {
      filtered = filtered.filter(r => r.Type && selectedTypes.has(r.Type));
    }
    
    // Filter by country
    if (selectedCountries.size > 0) {
      filtered = filtered.filter(r => {
        if (!r.countries) return false;
        const rowCountries = r.countries.split('|').map(c => c.trim());
        return rowCountries.some(c => selectedCountries.has(c));
      });
    }
    
    return filtered;
  });

  // Toggle facet selection - Create new Set for reactivity
  function toggleType(type: string) {
    const newSet = new Set(selectedTypes);
    if (newSet.has(type)) {
      newSet.delete(type);
    } else {
      newSet.add(type);
    }
    selectedTypes = newSet;
  }

  function toggleCountry(country: string) {
    const newSet = new Set(selectedCountries);
    if (newSet.has(country)) {
      newSet.delete(country);
    } else {
      newSet.add(country);
    }
    selectedCountries = newSet;
  }

  function clearAllFilters() {
    selectedTypes = new Set();
    selectedCountries = new Set();
  }

  const hasActiveFilters = $derived(selectedTypes.size > 0 || selectedCountries.size > 0);

  // Translation map for entity types
  const entityTypeTranslationMap: Record<string, string> = {
    'Events': 'entity.events',
    'Locations': 'entity.locations',
    'Organizations': 'entity.organizations',
    'Persons': 'entity.persons',
    'Topics': 'entity.topics',
    'Authority Files': 'entity.authority files'
  };

  // Helper function to translate entity types
  function translateType(type: string): string {
    const key = entityTypeTranslationMap[type];
    return key ? t(key) : type;
  }

  function entityUrl(r: EntityRow): string {
    const id = r['o:id'];
    if (id == null) return '#';
    return `${itemBase}${id}`;
  }

  // Define columns reactively to update labels when language changes
  const columns = $derived<ColumnDef<EntityRow>[]>([
    {
      key: 'Titre',
      label: t('table.title'),
      width: 'w-1/4',
      align: 'left'
    },
    {
      key: 'Type',
      label: t('table.type'),
      width: 'w-1/6',
      align: 'left'
    },
    {
      key: 'frequency',
      label: t('table.frequency'),
      width: 'w-20',
      align: 'right'
    },
    {
      key: 'first_occurrence',
      label: t('table.first'),
      width: 'w-1/6',
      align: 'left'
    },
    {
      key: 'last_occurrence',
      label: t('table.last'),
      width: 'w-1/6',
      align: 'left'
    },
    {
      key: 'countries',
      label: t('table.countries'),
      width: 'w-1/5',
      align: 'left'
    }
  ]);

  onMount(async () => {
    try {
      const url = `${base}/data/index-entities.json`;
      const res = await fetch(url);
      const json = (await res.json()) as EntityRow[];
      rows = json;
    } catch (e) {
      console.error(e);
      error = t('table.load_error');
    } finally {
      loading = false;
    }
  });
</script>

<div class="space-y-4">
  <!-- Facet Filters -->
  <div class="flex flex-wrap items-center gap-2">
    <!-- Type Filter -->
    <DropdownMenu.Root>
      <DropdownMenu.Trigger>
        {#snippet child({ props })}
          <Button {...props} variant="outline" size="sm" class="h-8 gap-1">
            <FilterIcon class="size-3.5" />
            {t('table.type')}
            {#if selectedTypes.size > 0}
              <Badge variant="secondary" class="ml-1 h-5 w-5 rounded-full p-0 flex items-center justify-center">
                {selectedTypes.size}
              </Badge>
            {/if}
          </Button>
        {/snippet}
      </DropdownMenu.Trigger>
      <DropdownMenu.Content align="start" class="w-48">
        <DropdownMenu.Label>{t('table.type')}</DropdownMenu.Label>
        <DropdownMenu.Separator />
        <div class="max-h-64 overflow-y-auto">
          {#each availableTypes as type}
            <DropdownMenu.CheckboxItem
              checked={selectedTypes.has(type)}
              onCheckedChange={() => toggleType(type)}
            >
              {translateType(type)}
            </DropdownMenu.CheckboxItem>
          {/each}
        </div>
      </DropdownMenu.Content>
    </DropdownMenu.Root>

    <!-- Country Filter -->
    <DropdownMenu.Root>
      <DropdownMenu.Trigger>
        {#snippet child({ props })}
          <Button {...props} variant="outline" size="sm" class="h-8 gap-1">
            <FilterIcon class="size-3.5" />
            {t('table.countries')}
            {#if selectedCountries.size > 0}
              <Badge variant="secondary" class="ml-1 h-5 w-5 rounded-full p-0 flex items-center justify-center">
                {selectedCountries.size}
              </Badge>
            {/if}
          </Button>
        {/snippet}
      </DropdownMenu.Trigger>
      <DropdownMenu.Content align="start" class="w-48">
        <DropdownMenu.Label>{t('table.countries')}</DropdownMenu.Label>
        <DropdownMenu.Separator />
        <div class="max-h-64 overflow-y-auto">
          {#each availableCountries as country}
            <DropdownMenu.CheckboxItem
              checked={selectedCountries.has(country)}
              onCheckedChange={() => toggleCountry(country)}
            >
              {country}
            </DropdownMenu.CheckboxItem>
          {/each}
        </div>
      </DropdownMenu.Content>
    </DropdownMenu.Root>

    <!-- Clear Filters Button -->
    {#if hasActiveFilters}
      <Button variant="ghost" size="sm" class="h-8 px-2" onclick={clearAllFilters}>
        <XIcon class="size-3.5 mr-1" />
        {t('table.clear_filters')}
      </Button>
    {/if}
  </div>

  <!-- Active Filter Badges -->
  {#if hasActiveFilters}
    <div class="flex flex-wrap items-center gap-2">
      {#each [...selectedTypes] as type}
        <Badge variant="secondary" class="gap-1 pr-1">
          <span class="text-xs">{t('table.type')}: {translateType(type)}</span>
          <button
            type="button"
            class="ml-1 rounded-full hover:bg-muted p-0.5"
            onclick={() => toggleType(type)}
            aria-label="Remove filter"
          >
            <XIcon class="size-3" />
          </button>
        </Badge>
      {/each}
      {#each [...selectedCountries] as country}
        <Badge variant="secondary" class="gap-1 pr-1">
          <span class="text-xs">{t('table.countries')}: {country}</span>
          <button
            type="button"
            class="ml-1 rounded-full hover:bg-muted p-0.5"
            onclick={() => toggleCountry(country)}
            aria-label="Remove filter"
          >
            <XIcon class="size-3" />
          </button>
        </Badge>
      {/each}
    </div>
  {/if}

  <!-- Data Table -->
  <DataTable
    data={filteredRows}
    {columns}
    {loading}
    {error}
    searchPlaceholder={t('table.search_placeholder')}
    noResultsText={t('table.no_results')}
    loadingText={t('common.loading')}
    defaultSortKey="frequency"
    defaultSortDir="desc"
    pageSize={50}
  >
    {#snippet cellRenderer({ row, column, value })}
      {#if column.key === 'Titre'}
        {#if row.Titre}
          <a
            href={entityUrl(row)}
            target="_blank"
            rel="noopener noreferrer"
            class="underline-offset-2 hover:underline block truncate"
            title={row.Titre}
          >
            {row.Titre}
          </a>
        {:else}
          <span class="truncate block">—</span>
        {/if}
      {:else if column.key === 'Type'}
        <span class="truncate block" title={String(value ?? '')}>
          {value ? translateType(String(value)) : '—'}
        </span>
      {:else}
        <span class="truncate block" title={String(value ?? '')}>
          {value ?? '—'}
        </span>
      {/if}
    {/snippet}
  </DataTable>
</div>
