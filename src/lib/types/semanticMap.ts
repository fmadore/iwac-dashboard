export interface SemanticMapPoint {
	id: number;
	title: string;
	x: number;
	y: number;
	country: string;
	newspaper: string;
	year: number;
	topicId: number;
	topicLabel: string;
	sentiment: string;
	polarity: string;
}

export interface SemanticMapTopic {
	id: number;
	label: string;
}

/** Compact wire format from JSON (arrays instead of objects, index-based lookups) */
export interface SemanticMapRawData {
	/** Points as arrays: [id, title, x, y, countryIdx, newspaperIdx, year, topicId, sentimentCode, polarityCode] */
	p: [number, string, number, number, number, number, number, number, string, string][];
	/** Country lookup array */
	c: string[];
	/** Newspaper lookup array */
	n: string[];
	/** Topic lookup */
	t: SemanticMapTopic[];
	/** Sentiment code reverse map */
	sc: Record<string, string>;
	/** Polarity code reverse map */
	pc: Record<string, string>;
	/** Year range */
	yr: [number, number];
	meta: {
		totalRecords: number;
		dataSource: string;
		generatedAt: string;
		umapParams: {
			n_neighbors: number;
			min_dist: number;
			metric: string;
		};
		embeddingDim: number;
		skippedNoEmbedding: number;
	};
}

export type ColorByOption = 'country' | 'topic' | 'newspaper' | 'sentiment' | 'polarity' | 'decade';

/** Manifest listing available per-country files */
export interface SemanticMapIndex {
	countries: { slug: string; name: string; count: number }[];
	total: number;
}

// ═══════════════════════════════════════════════════
// Columnar data store — zero bulk hydration
// ═══════════════════════════════════════════════════

export interface SemanticMapColumnar {
	length: number;
	/** [x0, y0, x1, y1, ...] ready for WebGL upload */
	positions: Float32Array;
	/** Per-point columns for fast index-based color/filter */
	countryIndices: Int8Array;
	newspaperIndices: Int16Array;
	years: Int16Array;
	topicIds: Int8Array;
	sentimentCodes: Uint8Array;
	polarityCodes: Uint8Array;
	/** Raw compact points — kept for title/id access on hover/click */
	raw: SemanticMapRawData;
}

export interface LegendEntry {
	key: number;
	label: string;
	color: string;
}

/** Build columnar typed arrays from raw JSON — single pass, ~5ms for 12k points */
export function buildColumnar(raw: SemanticMapRawData): SemanticMapColumnar {
	const n = raw.p.length;
	const positions = new Float32Array(n * 2);
	const countryIndices = new Int8Array(n);
	const newspaperIndices = new Int16Array(n);
	const years = new Int16Array(n);
	const topicIds = new Int8Array(n);
	const sentimentCodes = new Uint8Array(n);
	const polarityCodes = new Uint8Array(n);

	// Map sentiment/polarity short codes to numeric indices
	const sentimentCodeMap: Record<string, number> = {};
	const polarityCodeMap: Record<string, number> = {};
	let si = 0;
	for (const code of Object.keys(raw.sc)) {
		sentimentCodeMap[code] = si++;
	}
	let pi = 0;
	for (const code of Object.keys(raw.pc)) {
		polarityCodeMap[code] = pi++;
	}

	for (let i = 0; i < n; i++) {
		const r = raw.p[i];
		positions[i * 2] = r[2];
		positions[i * 2 + 1] = r[3];
		countryIndices[i] = r[4];
		newspaperIndices[i] = r[5];
		years[i] = r[6];
		topicIds[i] = r[7];
		sentimentCodes[i] = sentimentCodeMap[r[8] as string] ?? 255;
		polarityCodes[i] = polarityCodeMap[r[9] as string] ?? 255;
	}

	return {
		length: n,
		positions,
		countryIndices,
		newspaperIndices,
		years,
		topicIds,
		sentimentCodes,
		polarityCodes,
		raw
	};
}

/** Hydrate a single point on demand (for hover/click detail) */
export function hydratePoint(data: SemanticMapColumnar, index: number): SemanticMapPoint {
	const r = data.raw.p[index];
	const topicId = r[7];
	const topic = data.raw.t.find((t) => t.id === topicId);
	return {
		id: r[0],
		title: r[1],
		x: r[2],
		y: r[3],
		country: r[4] >= 0 ? data.raw.c[r[4]] : '',
		newspaper: r[5] >= 0 ? data.raw.n[r[5]] : '',
		year: r[6],
		topicId,
		topicLabel: topic?.label || '',
		sentiment: data.raw.sc[r[8] as string] || '',
		polarity: data.raw.pc[r[9] as string] || ''
	};
}

/** Compute per-point color palette index + legend entries */
export function computeColorIndices(
	data: SemanticMapColumnar,
	colorBy: ColorByOption,
	palette: string[]
): { groupPerPoint: Uint8Array; legend: LegendEntry[] } {
	const n = data.length;
	const groupPerPoint = new Uint8Array(n);
	const legend: LegendEntry[] = [];

	switch (colorBy) {
		case 'country': {
			for (let i = 0; i < n; i++) {
				const ci = data.countryIndices[i];
				groupPerPoint[i] = ci >= 0 ? ci : 255;
			}
			for (let i = 0; i < data.raw.c.length; i++) {
				legend.push({ key: i, label: data.raw.c[i], color: palette[i % palette.length] });
			}
			break;
		}
		case 'newspaper': {
			for (let i = 0; i < n; i++) {
				const ni = data.newspaperIndices[i];
				groupPerPoint[i] = ni >= 0 ? ni : 255;
			}
			// Top 10 newspapers by count
			const counts = new Uint16Array(data.raw.n.length);
			for (let i = 0; i < n; i++) {
				const ni = data.newspaperIndices[i];
				if (ni >= 0) counts[ni]++;
			}
			const sorted = [...data.raw.n.keys()].sort((a, b) => counts[b] - counts[a]).slice(0, 10);
			for (const idx of sorted) {
				legend.push({
					key: idx,
					label: data.raw.n[idx],
					color: palette[idx % palette.length]
				});
			}
			break;
		}
		case 'topic': {
			// Map topic IDs to sequential group indices
			const topicIdToGroup = new Map<number, number>();
			for (let g = 0; g < data.raw.t.length; g++) {
				topicIdToGroup.set(data.raw.t[g].id, g);
			}
			for (let i = 0; i < n; i++) {
				const tid = data.topicIds[i];
				groupPerPoint[i] = topicIdToGroup.get(tid) ?? 255;
			}
			// Top 15 topics by count
			const counts = new Uint16Array(data.raw.t.length);
			for (let i = 0; i < n; i++) {
				const g = groupPerPoint[i];
				if (g < 255) counts[g]++;
			}
			const sorted = [...data.raw.t.keys()].sort((a, b) => counts[b] - counts[a]).slice(0, 15);
			for (const idx of sorted) {
				legend.push({
					key: idx,
					label: data.raw.t[idx].label || `Topic ${data.raw.t[idx].id}`,
					color: palette[idx % palette.length]
				});
			}
			break;
		}
		case 'sentiment': {
			const labels = Object.values(data.raw.sc);
			for (let i = 0; i < n; i++) {
				groupPerPoint[i] = data.sentimentCodes[i];
			}
			for (let i = 0; i < labels.length; i++) {
				legend.push({ key: i, label: labels[i], color: palette[i % palette.length] });
			}
			break;
		}
		case 'polarity': {
			const labels = Object.values(data.raw.pc);
			for (let i = 0; i < n; i++) {
				groupPerPoint[i] = data.polarityCodes[i];
			}
			for (let i = 0; i < labels.length; i++) {
				legend.push({ key: i, label: labels[i], color: palette[i % palette.length] });
			}
			break;
		}
		case 'decade': {
			const [minY, maxY] = data.raw.yr;
			const baseDecade = Math.floor(minY / 10) * 10;
			for (let i = 0; i < n; i++) {
				const y = data.years[i];
				groupPerPoint[i] = y > 0 ? Math.floor((y - baseDecade) / 10) : 255;
			}
			const endDecade = Math.floor(maxY / 10) * 10;
			let idx = 0;
			for (let d = baseDecade; d <= endDecade; d += 10) {
				legend.push({ key: idx, label: `${d}s`, color: palette[idx % palette.length] });
				idx++;
			}
			break;
		}
	}

	return { groupPerPoint, legend };
}
