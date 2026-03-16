import { browser } from '$app/environment';

/**
 * Reactive container size tracking via ResizeObserver.
 * Returns reactive width and height values that update when the element resizes.
 *
 * @param element - A getter function returning the element to observe (or null/undefined).
 *
 * @example
 * ```svelte
 * <script>
 *   import { useResizeObserver } from '$lib/hooks/index.js';
 *   let containerEl = $state<HTMLElement | null>(null);
 *   const { width, height } = useResizeObserver(() => containerEl);
 * </script>
 * <div bind:this={containerEl}>Width: {width}</div>
 * ```
 */
export function useResizeObserver(element: () => HTMLElement | null | undefined) {
	let width = $state(0);
	let height = $state(0);

	$effect(() => {
		const el = element();
		if (!browser || !el) return;

		const update = () => {
			width = el.clientWidth;
			height = el.clientHeight;
		};

		update();
		const ro = new ResizeObserver(update);
		ro.observe(el);
		return () => ro.disconnect();
	});

	return {
		get width() {
			return width;
		},
		get height() {
			return height;
		}
	};
}
