export interface Word {
	text: string;
	size: number;
	x?: number;
	y?: number;
	rotate?: number;
	font?: string;
	style?: string;
	weight?: string;
	color?: string;
	padding?: number;
}

export interface CloudLayout {
	size(): [number, number];
	size(size: [number, number]): this;

	words(): Word[];
	words(words: Word[]): this;

	padding(): number | ((word: Word, index: number) => number);
	padding(padding: number | ((word: Word, index: number) => number)): this;

	rotate(): number | ((word: Word, index: number) => number);
	rotate(rotate: number | ((word: Word, index: number) => number)): this;

	font(): string | ((word: Word, index: number) => string);
	font(font: string | ((word: Word, index: number) => string)): this;

	fontStyle(): string | ((word: Word, index: number) => string);
	fontStyle(fontStyle: string | ((word: Word, index: number) => string)): this;

	fontWeight(): string | ((word: Word, index: number) => string);
	fontWeight(fontWeight: string | ((word: Word, index: number) => string)): this;

	fontSize(): number | ((word: Word, index: number) => number);
	fontSize(fontSize: number | ((word: Word, index: number) => number)): this;

	text(): string | ((word: Word, index: number) => string);
	text(text: string | ((word: Word, index: number) => string)): this;

	spiral(): string | ((size: [number, number]) => (t: number) => [number, number]);
	spiral(spiral: string | ((size: [number, number]) => (t: number) => [number, number])): this;

	on(type: 'word', listener: (word: Word) => void): this;
	on(type: 'end', listener: (words: Word[]) => void): this;

	start(): this;
	stop(): this;

	timeInterval(): number;
	timeInterval(interval: number): this;

	random(): () => number;
	random(random: () => number): this;

	canvas(): HTMLCanvasElement;
	canvas(canvas: HTMLCanvasElement): this;
}

declare module 'd3-cloud' {
	export default function cloud(): CloudLayout;
}

declare module 'd3-selection' {
	export interface Selection<
		GElement extends d3.BaseType,
		Datum,
		PElement extends d3.BaseType,
		PDatum
	> {
		selectAll<DescElement extends d3.BaseType>(
			selector: string
		): Selection<DescElement, Datum, GElement, Datum>;
		select<DescElement extends d3.BaseType>(
			selector: string
		): Selection<DescElement, Datum, PElement, PDatum>;
		data<NewDatum>(data: NewDatum[]): Selection<GElement, NewDatum, PElement, PDatum>;
		enter(): Selection<d3.EnterElement, Datum, PElement, PDatum>;
		append<K extends keyof SVGElementTagNameMap>(
			type: K
		): Selection<SVGElementTagNameMap[K], Datum, PElement, PDatum>;
		append(type: string): Selection<SVGElement, Datum, PElement, PDatum>;
		text(value: string | ((d: Datum, i: number, group: GElement[]) => string)): this;
		attr(
			name: string,
			value:
				| string
				| number
				| boolean
				| null
				| ((d: Datum, i: number, group: GElement[]) => string | number | boolean | null)
		): this;
		style(
			name: string,
			value:
				| string
				| number
				| null
				| ((d: Datum, i: number, group: GElement[]) => string | number | null)
		): this;
		on(
			typenames: string,
			listener: ((this: GElement, event: Event, d: Datum) => void) | null
		): this;
		transition(): Transition<GElement, Datum, PElement, PDatum>;
		remove(): this;
	}

	export interface Transition<
		GElement extends d3.BaseType,
		Datum,
		PElement extends d3.BaseType,
		PDatum
	> {
		attr(
			name: string,
			value:
				| string
				| number
				| boolean
				| null
				| ((d: Datum, i: number, group: GElement[]) => string | number | boolean | null)
		): this;
		style(
			name: string,
			value:
				| string
				| number
				| null
				| ((d: Datum, i: number, group: GElement[]) => string | number | null)
		): this;
		duration(milliseconds: number): this;
		delay(milliseconds: number | ((d: Datum, i: number, group: GElement[]) => number)): this;
	}

	export interface BaseType {}
	export interface EnterElement {
		ownerDocument: Document;
		namespaceURI: string;
		appendChild(newChild: Node): Node;
	}

	export function select<GElement extends d3.BaseType>(
		selector: string
	): Selection<GElement, unknown, null, undefined>;
	export function select<GElement extends d3.BaseType>(
		element: GElement
	): Selection<GElement, unknown, null, undefined>;
	export function selectAll<GElement extends d3.BaseType>(
		selector: string
	): Selection<GElement, unknown, null, undefined>;
}

declare module 'd3-scale-chromatic' {
	export function schemeCategory10(index: number): string;
	export function schemeSet3(index: number): string;
	export function schemeDark2(index: number): string;
	export function schemeAccent(index: number): string;
	export function schemePastel1(index: number): string;
	export function schemePastel2(index: number): string;
	export function schemeSet1(index: number): string;
	export function schemeSet2(index: number): string;
	export function schemeTableau10(index: number): string;

	export const schemeCategory10: readonly string[];
	export const schemeSet3: readonly string[];
	export const schemeDark2: readonly string[];
	export const schemeAccent: readonly string[];
	export const schemePastel1: readonly string[];
	export const schemePastel2: readonly string[];
	export const schemeSet1: readonly string[];
	export const schemeSet2: readonly string[];
	export const schemeTableau10: readonly string[];
}
