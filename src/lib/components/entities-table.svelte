<script lang="ts">
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { t, languageStore } from '$lib/stores/translationStore.js';
  import {
    Table,
    TableHeader,
    TableHead,
    TableBody,
    TableRow,
    TableCell
  } from '$lib/components/ui/table/index.js';

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

  let search = $state('');
  type SortKey = 'Titre' | 'Type' | 'frequency' | 'first_occurrence' | 'last_occurrence' | 'countries';
  let sortKey = $state<SortKey>('frequency');
  let sortDir = $state<'asc' | 'desc'>('desc');

  // Pagination state
  let currentPage = $state(1);
  let pageSize = $state(50);

  const enBase = 'https://islam.zmo.de/s/westafrica/item/';
  const frBase = 'https://islam.zmo.de/s/afrique_ouest/item/';
  const itemBase = $derived($languageStore === 'fr' ? frBase : enBase);

  function entityUrl(r: EntityRow): string {
    const id = r['o:id'];
    if (id == null) return '#';
    return `${itemBase}${id}`;
  }

  onMount(async () => {
    try {
      const url = `${base}/data/index-entities.json`;
      const res = await fetch(url);
      const json = (await res.json()) as EntityRow[];
      rows = json;
    } catch (e) {
      console.error(e);
      error = $t('table.load_error');
    } finally {
      loading = false;
    }
  });

  function setSort(key: SortKey) {
    if (sortKey === key) {
      sortDir = sortDir === 'asc' ? 'desc' : 'asc';
    } else {
      sortKey = key;
      sortDir = key === 'Titre' || key === 'Type' || key === 'countries' ? 'asc' : 'desc';
    }
    // Reset to first page when sorting changes
    currentPage = 1;
  }

  function cmp(a: unknown, b: unknown): number {
    if (a == null && b == null) return 0;
    if (a == null) return -1;
    if (b == null) return 1;
    if (typeof a === 'number' && typeof b === 'number') return a - b;
    const as = String(a).toLowerCase();
    const bs = String(b).toLowerCase();
    if (as < bs) return -1;
    if (as > bs) return 1;
    return 0;
  }

  const filtered = $derived(rows.filter((r) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      (r.Titre ?? '').toLowerCase().includes(q) ||
      (r.Type ?? '').toLowerCase().includes(q) ||
      (r.countries ?? '').toLowerCase().includes(q)
    );
  }));

  const sorted = $derived([...filtered].sort((a, b) => {
    const va = a[sortKey] as unknown;
    const vb = b[sortKey] as unknown;
    const c = cmp(va, vb);
    return sortDir === 'asc' ? c : -c;
  }));

  // Pagination derived values
  const totalPages = $derived(Math.ceil(sorted.length / pageSize));
  const startIndex = $derived((currentPage - 1) * pageSize);
  const endIndex = $derived(Math.min(startIndex + pageSize, sorted.length));
  const paginatedRows = $derived(sorted.slice(startIndex, endIndex));

  // Watch for search changes and reset pagination
  $effect(() => {
    search; // trigger effect when search changes
    currentPage = 1;
  });

  function goToPage(page: number) {
    if (page >= 1 && page <= totalPages) {
      currentPage = page;
    }
  }

  function nextPage() {
    if (currentPage < totalPages) {
      currentPage++;
    }
  }

  function prevPage() {
    if (currentPage > 1) {
      currentPage--;
    }
  }
</script>

<div class="h-full flex flex-col space-y-3">
  <div class="flex items-center justify-between gap-3 flex-shrink-0">
    <Input
      placeholder={$t('table.search_placeholder')}
      bind:value={search}
      class="max-w-md"
    />
    <div class="text-sm text-muted-foreground">
      {loading ? $t('common.loading') : error ? error : `${startIndex + 1}-${endIndex} of ${sorted.length} entries`}
    </div>
  </div>

  <div class="flex-1 overflow-hidden rounded-md border">
    <div class="h-full overflow-auto">
      <Table>
        <TableHeader class="sticky top-0 bg-background z-10">
          <TableRow>
            <TableHead class="whitespace-nowrap">
              <button type="button" class="cursor-pointer hover:underline underline-offset-2" onclick={() => setSort('Titre')}>
                {$t('table.title')} {sortKey === 'Titre' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
              </button>
            </TableHead>
            <TableHead class="whitespace-nowrap">
              <button type="button" class="cursor-pointer hover:underline underline-offset-2" onclick={() => setSort('Type')}>
                {$t('table.type')} {sortKey === 'Type' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
              </button>
            </TableHead>
            <TableHead class="whitespace-nowrap">
              <button type="button" class="cursor-pointer hover:underline underline-offset-2" onclick={() => setSort('frequency')}>
                {$t('table.frequency')} {sortKey === 'frequency' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
              </button>
            </TableHead>
            <TableHead class="whitespace-nowrap">
              <button type="button" class="cursor-pointer hover:underline underline-offset-2" onclick={() => setSort('first_occurrence')}>
                {$t('table.first')} {sortKey === 'first_occurrence' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
              </button>
            </TableHead>
            <TableHead class="whitespace-nowrap">
              <button type="button" class="cursor-pointer hover:underline underline-offset-2" onclick={() => setSort('last_occurrence')}>
                {$t('table.last')} {sortKey === 'last_occurrence' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
              </button>
            </TableHead>
            <TableHead class="whitespace-nowrap">
              <button type="button" class="cursor-pointer hover:underline underline-offset-2" onclick={() => setSort('countries')}>
                {$t('table.countries')} {sortKey === 'countries' ? (sortDir === 'asc' ? '▲' : '▼') : ''}
              </button>
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {#if loading}
            <TableRow>
              <TableCell colspan={6}>{$t('common.loading')}</TableCell>
            </TableRow>
          {:else if error}
            <TableRow>
              <TableCell colspan={6} class="text-red-600">{error}</TableCell>
            </TableRow>
          {:else if sorted.length === 0}
            <TableRow>
              <TableCell colspan={6}>{$t('table.no_results')}</TableCell>
            </TableRow>
          {:else}
            {#each paginatedRows as r}
              <TableRow>
                <TableCell class="min-w-[16rem]">
                  {#if r.Titre}
                    <a href={entityUrl(r)} target="_blank" rel="noopener noreferrer" class="underline-offset-2 hover:underline">
                      {r.Titre}
                    </a>
                  {:else}
                    —
                  {/if}
                </TableCell>
                <TableCell class="whitespace-nowrap">{r.Type}</TableCell>
                <TableCell class="whitespace-nowrap">{r.frequency}</TableCell>
                <TableCell class="whitespace-nowrap">{r.first_occurrence}</TableCell>
                <TableCell class="whitespace-nowrap">{r.last_occurrence}</TableCell>
                <TableCell class="min-w-[12rem]">{r.countries}</TableCell>
              </TableRow>
            {/each}
          {/if}
        </TableBody>
      </Table>
    </div>
  </div>

  <!-- Pagination Controls -->
  {#if !loading && !error && sorted.length > 0}
    <div class="flex items-center justify-between space-x-2 py-4 flex-shrink-0">
      <div class="text-sm text-muted-foreground">
        Page {currentPage} of {totalPages}
      </div>
      <div class="flex items-center space-x-2">
        <Button 
          variant="outline" 
          size="sm" 
          disabled={currentPage === 1}
          onclick={prevPage}
        >
          Previous
        </Button>
        
        {#if totalPages <= 7}
          {#each Array(totalPages).fill(0) as _, i}
            <Button 
              variant={currentPage === i + 1 ? "default" : "outline"}
              size="sm"
              onclick={() => goToPage(i + 1)}
            >
              {i + 1}
            </Button>
          {/each}
        {:else}
          <!-- Show first page -->
          <Button 
            variant={currentPage === 1 ? "default" : "outline"}
            size="sm"
            onclick={() => goToPage(1)}
          >
            1
          </Button>
          
          {#if currentPage > 3}
            <span class="px-2">...</span>
          {/if}
          
          <!-- Show pages around current page -->
          {#each Array(3).fill(0) as _, i}
            {#if currentPage - 1 + i > 1 && currentPage - 1 + i < totalPages}
              <Button 
                variant={currentPage === currentPage - 1 + i ? "default" : "outline"}
                size="sm"
                onclick={() => goToPage(currentPage - 1 + i)}
              >
                {currentPage - 1 + i}
              </Button>
            {/if}
          {/each}
          
          {#if currentPage < totalPages - 2}
            <span class="px-2">...</span>
          {/if}
          
          <!-- Show last page -->
          <Button 
            variant={currentPage === totalPages ? "default" : "outline"}
            size="sm"
            onclick={() => goToPage(totalPages)}
          >
            {totalPages}
          </Button>
        {/if}
        
        <Button 
          variant="outline" 
          size="sm" 
          disabled={currentPage === totalPages}
          onclick={nextPage}
        >
          Next
        </Button>
      </div>
    </div>
  {/if}
</div>
