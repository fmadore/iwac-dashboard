<script lang="ts" generics="TData extends Record<string, any>">
  import { Input } from '$lib/components/ui/input/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import {
    Table,
    TableHeader,
    TableHead,
    TableBody,
    TableRow,
    TableCell
  } from '$lib/components/ui/table/index.js';
  import type { Snippet } from 'svelte';

  // Column definition type
  export type ColumnDef<T> = {
    key: string;
    label: string;
    sortable?: boolean;
    searchable?: boolean;
    width?: string; // e.g., "w-1/4", "w-20"
    align?: 'left' | 'center' | 'right';
    cellClass?: string;
    headerClass?: string;
    render?: (row: T) => string | number | null;
  };

  type DataTableProps<T> = {
    data: T[];
    columns: ColumnDef<T>[];
    loading?: boolean;
    error?: string | null;
    searchPlaceholder?: string;
    noResultsText?: string;
    loadingText?: string;
    pageSize?: number;
    searchKeys?: (keyof T)[];
    defaultSortKey?: string;
    defaultSortDir?: 'asc' | 'desc';
    cellRenderer?: Snippet<[{ row: T; column: ColumnDef<T>; value: any }]>;
    rowClass?: (row: T) => string;
  };

  let {
    data = [],
    columns,
    loading = false,
    error = null,
    searchPlaceholder = 'Search...',
    noResultsText = 'No results found',
    loadingText = 'Loading...',
    pageSize = 50,
    searchKeys = undefined,
    defaultSortKey = columns[0]?.key ?? '',
    defaultSortDir = 'asc',
    cellRenderer,
    rowClass
  }: DataTableProps<TData> = $props();

  // Table state
  let search = $state('');
  let sortKey = $state(defaultSortKey);
  let sortDir = $state<'asc' | 'desc'>(defaultSortDir);
  let currentPage = $state(1);

  // Comparison function for sorting
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

  // Get value from row based on key (supports nested keys)
  function getValue(row: TData, key: string): any {
    const keys = key.split('.');
    let value: any = row;
    for (const k of keys) {
      if (value == null) return null;
      value = value[k];
    }
    return value;
  }

  // Filter rows based on search
  const filtered = $derived(
    data.filter((row) => {
      if (!search) return true;
      const q = search.toLowerCase();

      // If searchKeys provided, only search those keys
      const keysToSearch = searchKeys ?? columns.filter(c => c.searchable !== false).map(c => c.key as keyof TData);
      
      return keysToSearch.some((key) => {
        const value = getValue(row, String(key));
        return String(value ?? '').toLowerCase().includes(q);
      });
    })
  );

  // Sort filtered rows
  const sorted = $derived(
    [...filtered].sort((a, b) => {
      const va = getValue(a, sortKey);
      const vb = getValue(b, sortKey);
      const c = cmp(va, vb);
      return sortDir === 'asc' ? c : -c;
    })
  );

  // Pagination
  const totalPages = $derived(Math.ceil(sorted.length / pageSize));
  const startIndex = $derived((currentPage - 1) * pageSize);
  const endIndex = $derived(Math.min(startIndex + pageSize, sorted.length));
  const paginatedRows = $derived(sorted.slice(startIndex, endIndex));

  // Reset pagination when search changes
  $effect(() => {
    search;
    currentPage = 1;
  });

  // Sort handler
  function setSort(key: string) {
    if (sortKey === key) {
      sortDir = sortDir === 'asc' ? 'desc' : 'asc';
    } else {
      sortKey = key;
      // Default sort direction based on column type (string = asc, number = desc)
      const firstValue = data[0] ? getValue(data[0], key) : null;
      sortDir = typeof firstValue === 'number' ? 'desc' : 'asc';
    }
    currentPage = 1;
  }

  // Pagination handlers
  function goToPage(page: number) {
    if (page >= 1 && page <= totalPages) {
      currentPage = page;
    }
  }

  function nextPage() {
    if (currentPage < totalPages) currentPage++;
  }

  function prevPage() {
    if (currentPage > 1) currentPage--;
  }

  // Get rendered cell value
  function getCellValue(row: TData, column: ColumnDef<TData>): any {
    if (column.render) {
      return column.render(row);
    }
    return getValue(row, column.key);
  }

  // Get cell alignment class
  function getAlignClass(align?: 'left' | 'center' | 'right'): string {
    if (align === 'center') return 'text-center';
    if (align === 'right') return 'text-right';
    return 'text-left';
  }
</script>

<div class="w-full flex flex-col space-y-3">
  <!-- Search and Info Bar -->
  <div class="flex items-center justify-between gap-3 flex-shrink-0 flex-wrap">
    <Input
      placeholder={searchPlaceholder}
      bind:value={search}
      class="max-w-md min-w-0 flex-shrink"
    />
    <div class="text-sm text-muted-foreground whitespace-nowrap">
      {#if loading}
        {loadingText}
      {:else if error}
        {error}
      {:else}
        {startIndex + 1}-{endIndex} of {sorted.length} entries
      {/if}
    </div>
  </div>

  <!-- Table -->
  <div class="w-full rounded-md border border-border">
    <div class="w-full overflow-x-auto">
      <Table class="w-full">
        <TableHeader class="sticky top-0 bg-background z-10">
          <TableRow>
            {#each columns as column}
              <TableHead class={`${column.width ?? ''} ${column.headerClass ?? ''} min-w-0`}>
                {#if column.sortable !== false}
                  <button
                    type="button"
                    class="cursor-pointer hover:underline underline-offset-2 {getAlignClass(column.align)} w-full"
                    onclick={() => setSort(column.key)}
                  >
                    <span class="truncate block">
                      {column.label}
                      {sortKey === column.key ? (sortDir === 'asc' ? '▲' : '▼') : ''}
                    </span>
                  </button>
                {:else}
                  <span class="truncate block {getAlignClass(column.align)}">
                    {column.label}
                  </span>
                {/if}
              </TableHead>
            {/each}
          </TableRow>
        </TableHeader>
        <TableBody>
          {#if loading}
            <TableRow>
              <TableCell colspan={columns.length} class="h-24 text-center text-muted-foreground">
                {loadingText}
              </TableCell>
            </TableRow>
          {:else if error}
            <TableRow>
              <TableCell colspan={columns.length} class="h-24 text-center text-destructive">
                {error}
              </TableCell>
            </TableRow>
          {:else if sorted.length === 0}
            <TableRow>
              <TableCell colspan={columns.length} class="h-24 text-center text-muted-foreground">
                {noResultsText}
              </TableCell>
            </TableRow>
          {:else}
            {#each paginatedRows as row}
              <TableRow class={rowClass?.(row) ?? ''}>
                {#each columns as column}
                  {@const value = getCellValue(row, column)}
                  <TableCell 
                    class={`${column.width ?? ''} ${column.cellClass ?? ''} min-w-0 max-w-0 p-2 ${getAlignClass(column.align)}`}
                  >
                    {#if cellRenderer}
                      {@render cellRenderer?.({ row, column, value })}
                    {:else}
                      <span class="truncate block" title={String(value ?? '')}>
                        {value ?? '—'}
                      </span>
                    {/if}
                  </TableCell>
                {/each}
              </TableRow>
            {/each}
          {/if}
        </TableBody>
      </Table>
    </div>
  </div>

  <!-- Pagination Controls -->
  {#if !loading && !error && sorted.length > 0}
    <div class="flex items-center justify-between space-x-2 py-4 flex-shrink-0 flex-wrap gap-2">
      <div class="text-sm text-muted-foreground whitespace-nowrap">
        Page {currentPage} of {totalPages}
      </div>
      <div class="flex items-center space-x-1 flex-wrap">
        <Button variant="outline" size="sm" disabled={currentPage === 1} onclick={prevPage}>
          Previous
        </Button>

        {#if totalPages <= 7}
          {#each Array(totalPages).fill(0) as _, i}
            <Button
              variant={currentPage === i + 1 ? 'default' : 'outline'}
              size="sm"
              onclick={() => goToPage(i + 1)}
              class="min-w-[2rem]"
            >
              {i + 1}
            </Button>
          {/each}
        {:else}
          <!-- First page -->
          <Button
            variant={currentPage === 1 ? 'default' : 'outline'}
            size="sm"
            onclick={() => goToPage(1)}
            class="min-w-[2rem]"
          >
            1
          </Button>

          {#if currentPage > 3}
            <span class="px-1 text-sm text-muted-foreground">...</span>
          {/if}

          <!-- Pages around current -->
          {#each Array(3).fill(0) as _, i}
            {#if currentPage - 1 + i > 1 && currentPage - 1 + i < totalPages}
              <Button
                variant={currentPage === currentPage - 1 + i ? 'default' : 'outline'}
                size="sm"
                onclick={() => goToPage(currentPage - 1 + i)}
                class="min-w-[2rem]"
              >
                {currentPage - 1 + i}
              </Button>
            {/if}
          {/each}

          {#if currentPage < totalPages - 2}
            <span class="px-1 text-sm text-muted-foreground">...</span>
          {/if}

          <!-- Last page -->
          <Button
            variant={currentPage === totalPages ? 'default' : 'outline'}
            size="sm"
            onclick={() => goToPage(totalPages)}
            class="min-w-[2rem]"
          >
            {totalPages}
          </Button>
        {/if}

        <Button variant="outline" size="sm" disabled={currentPage === totalPages} onclick={nextPage}>
          Next
        </Button>
      </div>
    </div>
  {/if}
</div>
