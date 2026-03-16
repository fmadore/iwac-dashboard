import { describe, it, expect } from 'vitest';
import {
	calculateXAxisRotation,
	calculateXAxisTicks,
	calculateBottomPadding,
	tooltipLabelFromPayload,
	tooltipItemsFromPayload,
	filterNonZeroPayload,
	createLabelFormatter,
	LABEL_BREAKPOINT_TIGHT,
	LABEL_BREAKPOINT_COMFORTABLE,
	PADDING_ROTATED_90,
	PADDING_ROTATED_45,
	MIN_LABEL_SPACE_ROTATED,
	MIN_LABEL_SPACE_DEFAULT,
	type TooltipPayloadItem
} from './chartUtils.js';

// ── calculateXAxisRotation ───────────────────────────────────────────

describe('calculateXAxisRotation', () => {
	it('returns 0 when perItemWidth is 0', () => {
		expect(calculateXAxisRotation(0)).toBe(0);
	});

	it('returns 90 when perItemWidth is below LABEL_BREAKPOINT_TIGHT (55)', () => {
		expect(calculateXAxisRotation(30)).toBe(90);
		expect(calculateXAxisRotation(54)).toBe(90);
	});

	it('returns 90 at exactly LABEL_BREAKPOINT_TIGHT - 1', () => {
		expect(calculateXAxisRotation(LABEL_BREAKPOINT_TIGHT - 1)).toBe(90);
	});

	it('returns 45 when perItemWidth equals LABEL_BREAKPOINT_TIGHT', () => {
		expect(calculateXAxisRotation(LABEL_BREAKPOINT_TIGHT)).toBe(45);
	});

	it('returns 45 when perItemWidth is between TIGHT and COMFORTABLE', () => {
		expect(calculateXAxisRotation(60)).toBe(45);
		expect(calculateXAxisRotation(89)).toBe(45);
	});

	it('returns 0 when perItemWidth equals LABEL_BREAKPOINT_COMFORTABLE', () => {
		expect(calculateXAxisRotation(LABEL_BREAKPOINT_COMFORTABLE)).toBe(0);
	});

	it('returns 0 when perItemWidth exceeds LABEL_BREAKPOINT_COMFORTABLE', () => {
		expect(calculateXAxisRotation(120)).toBe(0);
		expect(calculateXAxisRotation(200)).toBe(0);
	});

	it('uses explicit rotation override when positive', () => {
		expect(calculateXAxisRotation(30, 60)).toBe(60);
		expect(calculateXAxisRotation(200, 45)).toBe(45);
	});

	it('ignores explicit rotation when it is 0', () => {
		// explicitRotation of 0 is falsy, so auto-calculation kicks in
		expect(calculateXAxisRotation(30, 0)).toBe(90);
	});

	it('ignores negative explicit rotation', () => {
		// Negative is falsy in the condition `explicitRotation > 0`
		expect(calculateXAxisRotation(30, -10)).toBe(90);
	});
});

// ── calculateXAxisTicks ──────────────────────────────────────────────

describe('calculateXAxisTicks', () => {
	it('returns 1 when dataLength is 0', () => {
		expect(calculateXAxisTicks(50, 0, 0)).toBe(1);
	});

	it('returns 1 when dataLength is 1', () => {
		expect(calculateXAxisTicks(50, 0, 1)).toBe(1);
	});

	it('returns 1 when perItemWidth is 0 (falsy)', () => {
		expect(calculateXAxisTicks(0, 0, 10)).toBe(1);
	});

	it('uses MIN_LABEL_SPACE_ROTATED (50) when rotation >= 45', () => {
		// perItemWidth = 25, rotation = 45 → minLabelSpace = 50 → ceil(50/25) = 2
		expect(calculateXAxisTicks(25, 45, 10)).toBe(Math.ceil(MIN_LABEL_SPACE_ROTATED / 25));
	});

	it('uses MIN_LABEL_SPACE_DEFAULT (90) when rotation < 45', () => {
		// perItemWidth = 30, rotation = 0 → minLabelSpace = 90 → ceil(90/30) = 3
		expect(calculateXAxisTicks(30, 0, 10)).toBe(Math.ceil(MIN_LABEL_SPACE_DEFAULT / 30));
	});

	it('uses rotated space for rotation = 90', () => {
		// perItemWidth = 10, rotation = 90 → minLabelSpace = 50 → ceil(50/10) = 5
		expect(calculateXAxisTicks(10, 90, 20)).toBe(5);
	});

	it('returns at least 1 even when perItemWidth exceeds minLabelSpace', () => {
		// perItemWidth = 200, rotation = 0 → minLabelSpace = 90 → ceil(90/200) = 1
		expect(calculateXAxisTicks(200, 0, 10)).toBe(1);
	});

	it('handles fractional perItemWidth correctly', () => {
		// perItemWidth = 45.5, rotation = 0 → ceil(90/45.5) = ceil(1.978) = 2
		expect(calculateXAxisTicks(45.5, 0, 10)).toBe(2);
	});
});

// ── calculateBottomPadding ───────────────────────────────────────────

describe('calculateBottomPadding', () => {
	it('returns PADDING_ROTATED_90 (110) when rotation >= 90', () => {
		expect(calculateBottomPadding(90, 5)).toBe(PADDING_ROTATED_90);
		expect(calculateBottomPadding(120, 5)).toBe(PADDING_ROTATED_90);
	});

	it('returns PADDING_ROTATED_45 (80) when rotation is between 1 and 89', () => {
		expect(calculateBottomPadding(45, 5)).toBe(PADDING_ROTATED_45);
		expect(calculateBottomPadding(1, 5)).toBe(PADDING_ROTATED_45);
		expect(calculateBottomPadding(89, 5)).toBe(PADDING_ROTATED_45);
	});

	it('returns 60 when rotation is 0 and dataLength exceeds default threshold (10)', () => {
		expect(calculateBottomPadding(0, 11)).toBe(60);
		expect(calculateBottomPadding(0, 20)).toBe(60);
	});

	it('returns 40 when rotation is 0 and dataLength is within default threshold', () => {
		expect(calculateBottomPadding(0, 5)).toBe(40);
		expect(calculateBottomPadding(0, 10)).toBe(40);
	});

	it('respects custom threshold parameter', () => {
		expect(calculateBottomPadding(0, 6, 5)).toBe(60);
		expect(calculateBottomPadding(0, 5, 5)).toBe(40);
	});

	it('returns 40 when dataLength is 0 and rotation is 0', () => {
		expect(calculateBottomPadding(0, 0)).toBe(40);
	});
});

// ── tooltipLabelFromPayload ──────────────────────────────────────────

describe('tooltipLabelFromPayload', () => {
	it('returns empty string for empty array', () => {
		expect(tooltipLabelFromPayload([])).toBe('');
	});

	it('returns empty string for undefined/null-like input', () => {
		expect(tooltipLabelFromPayload(null as unknown as TooltipPayloadItem[])).toBe('');
		expect(tooltipLabelFromPayload(undefined as unknown as TooltipPayloadItem[])).toBe('');
	});

	it('extracts category from payload', () => {
		const payload: TooltipPayloadItem[] = [
			{ payload: { category: 'Books' } }
		];
		expect(tooltipLabelFromPayload(payload)).toBe('Books');
	});

	it('extracts year from payload when no category', () => {
		const payload: TooltipPayloadItem[] = [
			{ payload: { year: 2024 } }
		];
		expect(tooltipLabelFromPayload(payload)).toBe('2024');
	});

	it('extracts name from payload when no category or year', () => {
		const payload: TooltipPayloadItem[] = [
			{ payload: { name: 'Test Item' } }
		];
		expect(tooltipLabelFromPayload(payload)).toBe('Test Item');
	});

	it('falls back to item.label', () => {
		const payload: TooltipPayloadItem[] = [
			{ label: 'FallbackLabel' }
		];
		expect(tooltipLabelFromPayload(payload)).toBe('FallbackLabel');
	});

	it('falls back to item.name', () => {
		const payload: TooltipPayloadItem[] = [
			{ name: 'ItemName' }
		];
		expect(tooltipLabelFromPayload(payload)).toBe('ItemName');
	});

	it('uses labelField override to extract from payload', () => {
		const payload: TooltipPayloadItem[] = [
			{ payload: { customField: 'CustomValue', category: 'ShouldNotUse' } }
		];
		expect(tooltipLabelFromPayload(payload, 'customField')).toBe('CustomValue');
	});

	it('falls back to normal chain when labelField not found in payload', () => {
		const payload: TooltipPayloadItem[] = [
			{ payload: { category: 'FallbackCategory' } }
		];
		expect(tooltipLabelFromPayload(payload, 'nonExistent')).toBe('FallbackCategory');
	});

	it('returns empty string when no matching fields exist', () => {
		const payload: TooltipPayloadItem[] = [{ payload: {} }];
		expect(tooltipLabelFromPayload(payload)).toBe('');
	});

	it('prioritizes category over year and name', () => {
		const payload: TooltipPayloadItem[] = [
			{ name: 'N', label: 'L', payload: { category: 'C', year: 2020, name: 'PN' } }
		];
		expect(tooltipLabelFromPayload(payload)).toBe('C');
	});
});

// ── tooltipItemsFromPayload ──────────────────────────────────────────

describe('tooltipItemsFromPayload', () => {
	it('returns empty array for empty payload', () => {
		expect(tooltipItemsFromPayload([])).toEqual([]);
	});

	it('returns empty array for null payload', () => {
		expect(tooltipItemsFromPayload(null as unknown as TooltipPayloadItem[])).toEqual([]);
	});

	it('maps items with name and value', () => {
		const payload: TooltipPayloadItem[] = [
			{ key: 'a', name: 'Alpha', value: 10, color: '#f00' }
		];
		const result = tooltipItemsFromPayload(payload);
		expect(result).toHaveLength(1);
		expect(result[0]).toEqual({
			key: 'a',
			name: 'Alpha',
			value: 10,
			color: '#f00'
		});
	});

	it('uses config label and color when provided', () => {
		const payload: TooltipPayloadItem[] = [
			{ key: 'series1', name: 'series1', value: 42 }
		];
		const config = {
			series1: { label: 'Series One', color: '#00f' }
		};
		const result = tooltipItemsFromPayload(payload, config);
		expect(result).toHaveLength(1);
		expect(result[0].name).toBe('Series One');
		expect(result[0].color).toBe('#00f');
	});

	it('filters out items without a name', () => {
		const payload: TooltipPayloadItem[] = [
			{ key: '', value: 10 }
		];
		const result = tooltipItemsFromPayload(payload);
		// key is '' and name defaults to String('') which is '', filtered out because !name
		expect(result).toHaveLength(0);
	});

	it('filters out items with undefined value', () => {
		const payload: TooltipPayloadItem[] = [
			{ key: 'a', name: 'Alpha', value: undefined }
		];
		const result = tooltipItemsFromPayload(payload);
		expect(result).toHaveLength(0);
	});

	it('keeps items with zero value (0 !== undefined)', () => {
		const payload: TooltipPayloadItem[] = [
			{ key: 'a', name: 'Alpha', value: 0 }
		];
		const result = tooltipItemsFromPayload(payload);
		expect(result).toHaveLength(1);
		expect(result[0].value).toBe(0);
	});

	it('keeps items with string value', () => {
		const payload: TooltipPayloadItem[] = [
			{ key: 'a', name: 'Alpha', value: 'text' }
		];
		const result = tooltipItemsFromPayload(payload);
		expect(result).toHaveLength(1);
		expect(result[0].value).toBe('text');
	});

	it('extracts color from payload.color when item.color is undefined', () => {
		const payload: TooltipPayloadItem[] = [
			{ key: 'a', name: 'Alpha', value: 5, payload: { color: '#0f0' } }
		];
		const result = tooltipItemsFromPayload(payload);
		expect(result[0].color).toBe('#0f0');
	});

	it('handles multiple items and filters correctly', () => {
		const payload: TooltipPayloadItem[] = [
			{ key: 'a', name: 'Alpha', value: 10 },
			{ key: 'b', name: 'Beta', value: undefined },
			{ key: 'c', name: 'Gamma', value: 30, color: '#abc' }
		];
		const result = tooltipItemsFromPayload(payload);
		expect(result).toHaveLength(2);
		expect(result[0].key).toBe('a');
		expect(result[1].key).toBe('c');
	});
});

// ── filterNonZeroPayload ─────────────────────────────────────────────

describe('filterNonZeroPayload', () => {
	it('returns empty array for empty input', () => {
		expect(filterNonZeroPayload([])).toEqual([]);
	});

	it('returns empty array for null input', () => {
		expect(filterNonZeroPayload(null as unknown as TooltipPayloadItem[])).toEqual([]);
	});

	it('keeps items with positive numeric values >= 1', () => {
		const payload: TooltipPayloadItem[] = [
			{ name: 'a', value: 5 },
			{ name: 'b', value: 100 }
		];
		expect(filterNonZeroPayload(payload)).toHaveLength(2);
	});

	it('filters out items with value 0', () => {
		const payload: TooltipPayloadItem[] = [{ name: 'a', value: 0 }];
		expect(filterNonZeroPayload(payload)).toHaveLength(0);
	});

	it('filters out items with negative values', () => {
		const payload: TooltipPayloadItem[] = [{ name: 'a', value: -5 }];
		expect(filterNonZeroPayload(payload)).toHaveLength(0);
	});

	it('filters out items with fractional values less than 1', () => {
		const payload: TooltipPayloadItem[] = [{ name: 'a', value: 0.5 }];
		expect(filterNonZeroPayload(payload)).toHaveLength(0);
	});

	it('keeps items with value exactly 1', () => {
		const payload: TooltipPayloadItem[] = [{ name: 'a', value: 1 }];
		expect(filterNonZeroPayload(payload)).toHaveLength(1);
	});

	it('filters out items with NaN value', () => {
		const payload: TooltipPayloadItem[] = [{ name: 'a', value: NaN }];
		expect(filterNonZeroPayload(payload)).toHaveLength(0);
	});

	it('filters out items with undefined value', () => {
		const payload: TooltipPayloadItem[] = [{ name: 'a', value: undefined }];
		expect(filterNonZeroPayload(payload)).toHaveLength(0);
	});

	it('handles string values that are numeric', () => {
		const payload: TooltipPayloadItem[] = [
			{ name: 'a', value: '10' as unknown as number }
		];
		// '10' → Number('10') = 10, isFinite(10) && 10 >= 1 → true
		expect(filterNonZeroPayload(payload)).toHaveLength(1);
	});

	it('filters out non-numeric string values', () => {
		const payload: TooltipPayloadItem[] = [
			{ name: 'a', value: 'abc' as unknown as number }
		];
		// 'abc' → Number('abc') = NaN → filtered out
		expect(filterNonZeroPayload(payload)).toHaveLength(0);
	});

	it('handles mixed payload correctly', () => {
		const payload: TooltipPayloadItem[] = [
			{ name: 'keep', value: 5 },
			{ name: 'zero', value: 0 },
			{ name: 'neg', value: -1 },
			{ name: 'nan', value: NaN },
			{ name: 'big', value: 999 }
		];
		const result = filterNonZeroPayload(payload);
		expect(result).toHaveLength(2);
		expect(result[0].name).toBe('keep');
		expect(result[1].name).toBe('big');
	});
});

// ── createLabelFormatter ─────────────────────────────────────────────

describe('createLabelFormatter', () => {
	it('truncates labels exceeding maxChars', () => {
		const fmt = createLabelFormatter(10);
		expect(fmt('Hello World!')).toBe('Hello Wor\u2026');
	});

	it('does not truncate labels within maxChars', () => {
		const fmt = createLabelFormatter(10);
		expect(fmt('Short')).toBe('Short');
	});

	it('does not truncate label of exact length', () => {
		const fmt = createLabelFormatter(5);
		expect(fmt('Hello')).toBe('Hello');
	});

	it('truncates label one char over the limit', () => {
		const fmt = createLabelFormatter(5);
		expect(fmt('Hello!')).toBe('Hell\u2026');
	});

	it('clamps maxChars to minimum of 4', () => {
		const fmt = createLabelFormatter(2);
		// clampedMax = 4, so labels > 4 chars get truncated to 3 + ellipsis
		expect(fmt('ABCDE')).toBe('ABC\u2026');
		expect(fmt('ABCD')).toBe('ABCD');
	});

	it('handles maxChars of 0 by clamping to 4', () => {
		const fmt = createLabelFormatter(0);
		expect(fmt('ABCDE')).toBe('ABC\u2026');
	});

	it('handles empty string input', () => {
		const fmt = createLabelFormatter(10);
		expect(fmt('')).toBe('');
	});

	it('handles very large maxChars gracefully', () => {
		const fmt = createLabelFormatter(1000);
		const longLabel = 'A'.repeat(500);
		expect(fmt(longLabel)).toBe(longLabel);
	});
});

// ── Constants sanity checks ──────────────────────────────────────────

describe('chartUtils constants', () => {
	it('has expected breakpoint values', () => {
		expect(LABEL_BREAKPOINT_TIGHT).toBe(55);
		expect(LABEL_BREAKPOINT_COMFORTABLE).toBe(90);
	});

	it('has expected padding values', () => {
		expect(PADDING_ROTATED_90).toBe(110);
		expect(PADDING_ROTATED_45).toBe(80);
	});

	it('has expected minimum label space values', () => {
		expect(MIN_LABEL_SPACE_ROTATED).toBe(50);
		expect(MIN_LABEL_SPACE_DEFAULT).toBe(90);
	});
});
