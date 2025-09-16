declare global {
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

  export default function cloud(): CloudLayout;
}

export {};