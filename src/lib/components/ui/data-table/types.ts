import type { Snippet } from 'svelte';

/**
 * Column definition for DataTable component
 */
export type ColumnDef<T> = {
  /** Unique key for the column (supports nested keys with dot notation, e.g., 'user.name') */
  key: string;
  /** Display label for the column header */
  label: string;
  /** Whether the column is sortable (default: true) */
  sortable?: boolean;
  /** Whether the column is searchable (default: true) */
  searchable?: boolean;
  /** Tailwind width class (e.g., 'w-1/4', 'w-20') */
  width?: string;
  /** Text alignment in cells */
  align?: 'left' | 'center' | 'right';
  /** Additional CSS classes for cells */
  cellClass?: string;
  /** Additional CSS classes for header */
  headerClass?: string;
  /** Custom render function for cell values */
  render?: (row: T) => string | number | null;
};

/**
 * Props for DataTable component
 */
export type DataTableProps<T extends Record<string, any>> = {
  /** Array of data to display */
  data: T[];
  /** Column definitions */
  columns: ColumnDef<T>[];
  /** Loading state */
  loading?: boolean;
  /** Error message to display */
  error?: string | null;
  /** Placeholder text for search input */
  searchPlaceholder?: string;
  /** Text to display when no results found */
  noResultsText?: string;
  /** Text to display when loading */
  loadingText?: string;
  /** Number of rows per page */
  pageSize?: number;
  /** Specific keys to search (defaults to all searchable columns) */
  searchKeys?: (keyof T)[];
  /** Default column key to sort by */
  defaultSortKey?: string;
  /** Default sort direction */
  defaultSortDir?: 'asc' | 'desc';
  /** Custom cell renderer snippet */
  cellRenderer?: Snippet<[{ row: T; column: ColumnDef<T>; value: any }]>;
  /** Function to return custom CSS classes for a row */
  rowClass?: (row: T) => string;
};
