import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock SvelteKit modules before importing the module under test
vi.mock('$app/environment', () => ({ browser: false }));

import {
	ENTITY_COLOR_VARS,
	EDGE_COLOR_VARS,
	FALLBACK_COLORS,
	resolveCSSColor,
	getEntityColorsHex,
	getEdgeColorsHex
} from './theme.js';

// ── ENTITY_COLOR_VARS ────────────────────────────────────────────────

describe('ENTITY_COLOR_VARS', () => {
	const expectedEntityTypes = [
		'person',
		'organization',
		'event',
		'subject',
		'location',
		'topic',
		'article',
		'author',
		'authority'
	] as const;

	it('contains all 9 entity types', () => {
		const keys = Object.keys(ENTITY_COLOR_VARS);
		expect(keys).toHaveLength(9);
		for (const type of expectedEntityTypes) {
			expect(ENTITY_COLOR_VARS).toHaveProperty(type);
		}
	});

	it('all values are CSS variable names starting with --entity-', () => {
		for (const [key, value] of Object.entries(ENTITY_COLOR_VARS)) {
			expect(value).toMatch(/^--entity-/);
			expect(value).toBe(`--entity-${key}`);
		}
	});
});

// ── EDGE_COLOR_VARS ──────────────────────────────────────────────────

describe('EDGE_COLOR_VARS', () => {
	const expectedEdgeTypes = [
		'part_of',
		'has_part',
		'related_to',
		'succeeded_by',
		'located_in',
		'co_occurs_with',
		'co_authored_with'
	] as const;

	it('contains all expected edge types', () => {
		const keys = Object.keys(EDGE_COLOR_VARS);
		expect(keys).toHaveLength(7);
		for (const type of expectedEdgeTypes) {
			expect(EDGE_COLOR_VARS).toHaveProperty(type);
		}
	});

	it('all values are CSS variable names starting with --', () => {
		for (const value of Object.values(EDGE_COLOR_VARS)) {
			expect(value).toMatch(/^--/);
		}
	});
});

// ── FALLBACK_COLORS ──────────────────────────────────────────────────

describe('FALLBACK_COLORS', () => {
	it('has fallback for every entity type CSS variable', () => {
		for (const variable of Object.values(ENTITY_COLOR_VARS)) {
			expect(FALLBACK_COLORS).toHaveProperty(variable);
		}
	});

	it('has fallback for every edge type CSS variable', () => {
		for (const variable of Object.values(EDGE_COLOR_VARS)) {
			expect(FALLBACK_COLORS).toHaveProperty(variable);
		}
	});

	it('all values are valid hex color strings (#xxxxxx)', () => {
		const hexPattern = /^#[0-9a-fA-F]{6}$/;
		for (const [key, value] of Object.entries(FALLBACK_COLORS)) {
			expect(value, `FALLBACK_COLORS['${key}'] should be a valid hex color`).toMatch(hexPattern);
		}
	});

	it('includes chart variables (--chart-1 through --chart-16)', () => {
		for (let i = 1; i <= 16; i++) {
			expect(FALLBACK_COLORS).toHaveProperty(`--chart-${i}`);
		}
	});

	it('includes UI variables (--foreground, --background, etc.)', () => {
		const uiVars = [
			'--foreground',
			'--muted-foreground',
			'--background',
			'--popover',
			'--popover-foreground',
			'--border'
		];
		for (const varName of uiVars) {
			expect(FALLBACK_COLORS).toHaveProperty(varName);
		}
	});
});

// ── resolveCSSColor (fallback path, browser=false) ───────────────────

describe('resolveCSSColor', () => {
	it('returns fallback color for known CSS variable when browser is false', () => {
		const result = resolveCSSColor('--entity-person');
		expect(result).toBe(FALLBACK_COLORS['--entity-person']);
	});

	it('returns fallback for chart variables', () => {
		expect(resolveCSSColor('--chart-1')).toBe(FALLBACK_COLORS['--chart-1']);
		expect(resolveCSSColor('--chart-5')).toBe(FALLBACK_COLORS['--chart-5']);
	});

	it('returns default #666666 for unknown CSS variable', () => {
		expect(resolveCSSColor('--nonexistent-variable')).toBe('#666666');
	});

	it('returns default #666666 for empty string', () => {
		expect(resolveCSSColor('')).toBe('#666666');
	});

	it('returns actual fallback hex values (not OKLCH or other formats)', () => {
		const hexPattern = /^#[0-9a-fA-F]{6}$/;
		const result = resolveCSSColor('--entity-organization');
		expect(result).toMatch(hexPattern);
	});
});

// ── getEntityColorsHex ───────────────────────────────────────────────

describe('getEntityColorsHex', () => {
	it('returns an object with all entity type keys', () => {
		const colors = getEntityColorsHex();
		const entityTypes = Object.keys(ENTITY_COLOR_VARS);
		expect(Object.keys(colors)).toHaveLength(entityTypes.length);
		for (const type of entityTypes) {
			expect(colors).toHaveProperty(type);
		}
	});

	it('all values are hex color strings', () => {
		const hexPattern = /^#[0-9a-fA-F]{6}$/;
		const colors = getEntityColorsHex();
		for (const [type, color] of Object.entries(colors)) {
			expect(color, `Color for entity type '${type}' should be hex`).toMatch(hexPattern);
		}
	});

	it('values match FALLBACK_COLORS since browser is false', () => {
		const colors = getEntityColorsHex();
		for (const [type, variable] of Object.entries(ENTITY_COLOR_VARS)) {
			expect(colors[type]).toBe(FALLBACK_COLORS[variable]);
		}
	});
});

// ── getEdgeColorsHex ─────────────────────────────────────────────────

describe('getEdgeColorsHex', () => {
	it('returns an object with all edge type keys', () => {
		const colors = getEdgeColorsHex();
		const edgeTypes = Object.keys(EDGE_COLOR_VARS);
		expect(Object.keys(colors)).toHaveLength(edgeTypes.length);
		for (const type of edgeTypes) {
			expect(colors).toHaveProperty(type);
		}
	});

	it('all values are hex color strings', () => {
		const hexPattern = /^#[0-9a-fA-F]{6}$/;
		const colors = getEdgeColorsHex();
		for (const [type, color] of Object.entries(colors)) {
			expect(color, `Color for edge type '${type}' should be hex`).toMatch(hexPattern);
		}
	});

	it('values match FALLBACK_COLORS since browser is false', () => {
		const colors = getEdgeColorsHex();
		for (const [type, variable] of Object.entries(EDGE_COLOR_VARS)) {
			expect(colors[type]).toBe(FALLBACK_COLORS[variable]);
		}
	});
});
