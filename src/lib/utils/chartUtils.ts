/**
 * Shared chart utilities for axis formatting, tooltip parsing, and layout calculations.
 * Used by Bar.svelte, StackedBarChart.svelte, and other LayerChart/D3 chart components.
 */

// ── Axis Layout Constants ──────────────────────────────────────────────

/** Width threshold (px per item) that triggers 90° label rotation */
export const LABEL_BREAKPOINT_TIGHT = 55;

/** Width threshold (px per item) that triggers 45° label rotation */
export const LABEL_BREAKPOINT_COMFORTABLE = 90;

/** Bottom padding when labels are rotated 90° */
export const PADDING_ROTATED_90 = 110;

/** Bottom padding when labels are rotated 45° */
export const PADDING_ROTATED_45 = 80;

/** Minimum label spacing when rotated ≥45° */
export const MIN_LABEL_SPACE_ROTATED = 50;

/** Minimum label spacing when not rotated */
export const MIN_LABEL_SPACE_DEFAULT = 90;

// ── Axis Calculation Functions ─────────────────────────────────────────

/**
 * Calculate optimal X-axis label rotation based on available space per item.
 */
export function calculateXAxisRotation(perItemWidth: number, explicitRotation?: number): number {
	if (explicitRotation && explicitRotation > 0) return explicitRotation;
	if (perItemWidth <= 0) return 0;
	if (perItemWidth < LABEL_BREAKPOINT_TIGHT) return 90;
	if (perItemWidth < LABEL_BREAKPOINT_COMFORTABLE) return 45;
	return 0;
}

/**
 * Calculate how many X-axis tick labels to show (skip interval).
 * Returns a number N where every Nth label is shown.
 */
export function calculateXAxisTicks(
	perItemWidth: number,
	rotation: number,
	dataLength: number
): number {
	if (dataLength <= 1) return 1;
	if (!perItemWidth) return 1;
	const minLabelSpace = rotation >= 45 ? MIN_LABEL_SPACE_ROTATED : MIN_LABEL_SPACE_DEFAULT;
	return Math.max(1, Math.ceil(minLabelSpace / perItemWidth));
}

/**
 * Calculate bottom padding based on label rotation and data density.
 */
export function calculateBottomPadding(
	rotation: number,
	dataLength: number,
	threshold: number = 10
): number {
	if (rotation >= 90) return PADDING_ROTATED_90;
	if (rotation > 0) return PADDING_ROTATED_45;
	return dataLength > threshold ? 60 : 40;
}

// ── Tooltip Utilities ──────────────────────────────────────────────────

export interface TooltipPayloadItem {
	key?: string;
	name?: string;
	label?: string;
	value?: number | string;
	color?: string;
	payload?: Record<string, unknown>;
}

export interface ParsedTooltipItem {
	key: string;
	name: string;
	value: number | string;
	color: string | undefined;
}

/**
 * Extract the label (usually the category/year) from a tooltip payload.
 * Checks multiple common field paths for compatibility across chart types.
 */
export function tooltipLabelFromPayload(
	payload: TooltipPayloadItem[],
	labelField?: string
): string {
	const first = payload?.[0];
	if (!first) return '';

	// Check explicit field first
	if (labelField && first.payload) {
		const val = first.payload[labelField];
		if (val != null) return String(val);
	}

	// Common fallback paths
	return (
		String(
			first.payload?.category ??
				first.payload?.year ??
				first.payload?.name ??
				first.label ??
				first.name ??
				''
		)
	);
}

/**
 * Parse tooltip payload items into a normalized format.
 * Filters out items with no name or undefined values.
 */
export function tooltipItemsFromPayload(
	payload: TooltipPayloadItem[],
	config?: Record<string, { label?: string; color?: string }>
): ParsedTooltipItem[] {
	return (payload ?? [])
		.map((item): ParsedTooltipItem | null => {
			const key = item?.key ?? item?.name ?? '';
			const configEntry = key && config ? config[key] : undefined;
			const name = configEntry?.label ?? item?.name ?? String(key);
			const value = item?.value;
			if (!name || value === undefined) return null;
			return {
				key,
				name,
				value,
				color: item?.color ?? (item?.payload?.color as string | undefined) ?? configEntry?.color
			};
		})
		.filter((i): i is ParsedTooltipItem => i !== null);
}

/**
 * Filter tooltip payload to only items with non-zero numeric values.
 * Useful for stacked charts where zero-value series shouldn't appear in tooltips.
 */
export function filterNonZeroPayload(payload: TooltipPayloadItem[]): TooltipPayloadItem[] {
	return (payload ?? []).filter((item) => {
		const raw = item?.value;
		const value = typeof raw === 'number' ? raw : Number(raw);
		return Number.isFinite(value) && value >= 1;
	});
}

/**
 * Create a label truncation formatter based on available character space.
 */
export function createLabelFormatter(maxChars: number): (label: string) => string {
	const clampedMax = Math.max(4, maxChars);
	return (label: string) =>
		label.length > clampedMax ? label.slice(0, clampedMax - 1) + '…' : label;
}
