// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}

	interface Word {
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
}

declare module 'd3-cloud' {
	interface CloudLayout {
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
		fontSize(): number | ((word: Word, index: number) => number);
		fontSize(fontSize: number | ((word: Word, index: number) => number)): this;
		on(type: 'word', listener: (word: Word) => void): this;
		on(type: 'end', listener: (words: Word[]) => void): this;
		start(): this;
		stop(): this;
	}

	export default function cloud(): CloudLayout;
}

export {};
