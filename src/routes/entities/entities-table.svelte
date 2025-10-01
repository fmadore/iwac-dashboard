<script lang="ts">
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import { t, languageStore } from '$lib/stores/translationStore.svelte.js';
  import { DataTable } from '$lib/components/ui/data-table/index.js';
  import type { ColumnDef } from '$lib/components/ui/data-table/index.js';

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

  const enBase = 'https://islam.zmo.de/s/westafrica/item/';
  const frBase = 'https://islam.zmo.de/s/afrique_ouest/item/';
  const itemBase = $derived(languageStore.current === 'fr' ? frBase : enBase);

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

<DataTable
  data={rows}
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
    {:else}
      <span class="truncate block" title={String(value ?? '')}>
        {value ?? '—'}
      </span>
    {/if}
  {/snippet}
</DataTable>
