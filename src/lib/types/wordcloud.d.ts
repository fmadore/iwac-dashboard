declare module 'wordcloud' {
	interface WordCloudOptions {
		list: [string, number][];
		fontFamily?: string;
		backgroundColor?: string;
		color?:
			| string
			| ((
					word: string,
					weight: number,
					fontSize: number,
					distance: number,
					theta: number
			  ) => string);
		shape?: string;
		rotationSteps?: number;
		minRotation?: number;
		maxRotation?: number;
		weightFactor?: number;
		gridSize?: number;
		minSize?: number;
		drawOutOfBound?: boolean;
		shrinkToFit?: boolean;
		clearCanvas?: boolean;
		hover?: (
			item: [string, number] | null,
			dimension: { x: number; y: number; w: number; h: number } | null,
			event: Event
		) => void;
		click?: (
			item: [string, number] | null,
			dimension: { x: number; y: number; w: number; h: number } | null,
			event: Event
		) => void;
	}

	function WordCloud(element: HTMLCanvasElement, options: WordCloudOptions): void;

	namespace WordCloud {
		function stop(): void;
		const isSupported: boolean;
		const minFontSize: number;
	}

	export = WordCloud;
}
