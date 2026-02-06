import type { HierarchyRectangularNode } from 'd3-hierarchy';

export interface TreemapData {
	name: string;
	value?: number;
	children?: TreemapData[];
	/** Internal: country name injected during enrichment for color lookup */
	__countryName?: string;
	[key: string]: unknown;
}

export type TreemapNode = HierarchyRectangularNode<TreemapData>;

export interface TreemapPadding {
	inner: number;
	outer: number;
	top: number;
	right: number;
	bottom: number;
	left: number;
}

export interface TreemapColors {
	scheme: readonly string[] | string[]; // Support both readonly arrays and CSS custom properties
	background: string;
	border: string;
	text: string;
	textSecondary: string;
}

export interface TreemapAnimation {
	duration: number;
	ease: string;
}

export interface TreemapTextConfig {
	minWidth: number;
	minHeight: number;
	fontSize: {
		title: number;
		subtitle: number;
		small: number;
	};
}

export interface TreemapInteraction {
	hover: boolean;
	click: boolean;
	tooltip: boolean;
}

export interface TreemapZoom {
	enabled: boolean;
	scaleExtent: [number, number];
	resetOnDoubleClick: boolean;
}

export interface TreemapConfig {
	padding: TreemapPadding;
	tile: string | ((node: unknown, x0: number, y0: number, x1: number, y1: number) => void);
	round: boolean;
	colors: TreemapColors;
	animation: TreemapAnimation;
	text: TreemapTextConfig;
	interaction: TreemapInteraction;
	zoom: TreemapZoom;
}

export interface TreemapTooltipData {
	node: TreemapNode;
	x: number;
	y: number;
}
