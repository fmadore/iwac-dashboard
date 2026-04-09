<script lang="ts">
	import { t } from '$lib/stores/translationStore.svelte.js';
	import { useResizeObserver } from '$lib/hooks/index.js';

	interface Props {
		positions: Float32Array;
		pointCount: number;
		groupPerPoint: Uint8Array;
		palette: string[];
		highlightedGroup: number | null;
		onPointHover: (index: number | null, x: number, y: number) => void;
		onPointClick: (index: number | null) => void;
	}

	let {
		positions,
		pointCount,
		groupPerPoint,
		palette,
		highlightedGroup,
		onPointHover,
		onPointClick
	}: Props = $props();

	let canvas: HTMLCanvasElement | undefined = $state();
	let container: HTMLDivElement | undefined = $state();
	const size = useResizeObserver(() => container);
	let width = $derived(size.width || 800);
	let height = $derived(size.height || 600);

	let scale = $state(1);
	let offsetX = $state(0);
	let offsetY = $state(0);
	let isPanning = $state(false);
	let panStartX = 0;
	let panStartY = 0;

	const PADDING = 40;
	const BASE_POINT_SIZE = 5.0;

	// ═══════════════════════════════════════════════════
	// Renderer: WebGL primary, Canvas 2D fallback
	// ═══════════════════════════════════════════════════

	let useWebGL = $state(false);
	let rendererReady = $state(false);

	// --- Parsed palette (hex → [r, g, b] in 0-1, computed once per palette change) ---
	let parsedPalette: [number, number, number][] = [];

	function parsePalette(pal: string[]): [number, number, number][] {
		return pal.map((hex) => {
			const h = hex.replace('#', '');
			return [
				parseInt(h.substring(0, 2), 16) / 255,
				parseInt(h.substring(2, 4), 16) / 255,
				parseInt(h.substring(4, 6), 16) / 255
			];
		});
	}

	// --- WebGL state ---
	let gl: WebGLRenderingContext | null = null;
	let program: WebGLProgram | null = null;
	let posBuffer: WebGLBuffer | null = null;
	let colorBuffer: WebGLBuffer | null = null;
	let uTransform: WebGLUniformLocation | null = null;
	let uPointSize: WebGLUniformLocation | null = null;
	let uResolution: WebGLUniformLocation | null = null;
	let aPosLoc = -1;
	let aColLoc = -1;

	const VERT_SRC = `
		attribute vec2 aPosition;
		attribute vec4 aColor;
		uniform vec4 uTransform;
		uniform float uPointSize;
		uniform vec2 uResolution;
		varying vec4 vColor;
		void main() {
			float sx = aPosition.x * uTransform.x + uTransform.z;
			float sy = (1.0 - aPosition.y) * uTransform.y + uTransform.w;
			float cx = (sx / uResolution.x) * 2.0 - 1.0;
			float cy = 1.0 - (sy / uResolution.y) * 2.0;
			gl_Position = vec4(cx, cy, 0.0, 1.0);
			gl_PointSize = uPointSize;
			vColor = aColor;
		}
	`;

	const FRAG_SRC = `
		precision mediump float;
		varying vec4 vColor;
		void main() {
			vec2 c = gl_PointCoord - vec2(0.5);
			float dist = dot(c, c);
			if (dist > 0.25) discard;
			float alpha = 1.0 - smoothstep(0.2, 0.25, dist);
			gl_FragColor = vec4(vColor.rgb, vColor.a * alpha);
		}
	`;

	function compileShader(g: WebGLRenderingContext, src: string, type: number): WebGLShader | null {
		const shader = g.createShader(type);
		if (!shader) return null;
		g.shaderSource(shader, src);
		g.compileShader(shader);
		if (!g.getShaderParameter(shader, g.COMPILE_STATUS)) {
			g.deleteShader(shader);
			return null;
		}
		return shader;
	}

	function initWebGL(canvasEl: HTMLCanvasElement): boolean {
		gl = canvasEl.getContext('webgl', { antialias: true, alpha: true, premultipliedAlpha: false });
		if (!gl) return false;

		const vs = compileShader(gl, VERT_SRC, gl.VERTEX_SHADER);
		const fs = compileShader(gl, FRAG_SRC, gl.FRAGMENT_SHADER);
		if (!vs || !fs) return false;

		program = gl.createProgram();
		if (!program) return false;
		gl.attachShader(program, vs);
		gl.attachShader(program, fs);
		gl.linkProgram(program);
		if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return false;

		gl.useProgram(program);
		uTransform = gl.getUniformLocation(program, 'uTransform');
		uPointSize = gl.getUniformLocation(program, 'uPointSize');
		uResolution = gl.getUniformLocation(program, 'uResolution');
		aPosLoc = gl.getAttribLocation(program, 'aPosition');
		aColLoc = gl.getAttribLocation(program, 'aColor');

		posBuffer = gl.createBuffer();
		colorBuffer = gl.createBuffer();

		gl.enable(gl.BLEND);
		gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
		return true;
	}

	function uploadGLPositions() {
		if (!gl || !posBuffer) return;
		gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer);
		gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);
	}

	function buildGLColors(): Float32Array {
		const data = new Float32Array(pointCount * 4);
		const hl = highlightedGroup;
		const pal = parsedPalette;
		const fallback: [number, number, number] = [0.6, 0.6, 0.6];

		for (let i = 0; i < pointCount; i++) {
			const g = groupPerPoint[i];
			const rgb = g < pal.length ? pal[g] : fallback;
			const dimmed = hl !== null && g !== hl;
			const off = i * 4;
			data[off] = rgb[0];
			data[off + 1] = rgb[1];
			data[off + 2] = rgb[2];
			data[off + 3] = dimmed ? 0.15 : 0.85;
		}
		return data;
	}

	function uploadGLColors() {
		if (!gl || !colorBuffer) return;
		gl.bindBuffer(gl.ARRAY_BUFFER, colorBuffer);
		gl.bufferData(gl.ARRAY_BUFFER, buildGLColors(), gl.DYNAMIC_DRAW);
	}

	function drawWebGL() {
		if (!gl || !program || !canvas || pointCount === 0) return;

		const dpr = window.devicePixelRatio || 1;
		const cw = Math.round(width * dpr);
		const ch = Math.round(height * dpr);

		if (canvas.width !== cw || canvas.height !== ch) {
			canvas.width = cw;
			canvas.height = ch;
		}

		gl.viewport(0, 0, cw, ch);
		gl.clearColor(0, 0, 0, 0);
		gl.clear(gl.COLOR_BUFFER_BIT);
		gl.useProgram(program);

		gl.bindBuffer(gl.ARRAY_BUFFER, posBuffer);
		gl.enableVertexAttribArray(aPosLoc);
		gl.vertexAttribPointer(aPosLoc, 2, gl.FLOAT, false, 0, 0);

		gl.bindBuffer(gl.ARRAY_BUFFER, colorBuffer);
		gl.enableVertexAttribArray(aColLoc);
		gl.vertexAttribPointer(aColLoc, 4, gl.FLOAT, false, 0, 0);

		const plotW = width - PADDING * 2;
		const plotH = height - PADDING * 2;
		gl.uniform4f(uTransform, plotW * scale, plotH * scale, offsetX + PADDING, offsetY + PADDING);
		gl.uniform1f(uPointSize, Math.max(2, BASE_POINT_SIZE * Math.min(scale, 4)) * dpr);
		gl.uniform2f(uResolution, width, height);

		gl.drawArrays(gl.POINTS, 0, pointCount);
	}

	// --- Canvas 2D fallback ---
	let offscreen: OffscreenCanvas | HTMLCanvasElement | null = null;
	let offCtx: CanvasRenderingContext2D | OffscreenCanvasRenderingContext2D | null = null;
	let bufferDirty = true;
	const BUFFER_SIZE = 2048;
	const POINT_RADIUS = 2.5;

	function renderOffscreen() {
		if (!offscreen) {
			try {
				offscreen = new OffscreenCanvas(BUFFER_SIZE, BUFFER_SIZE);
				offCtx = offscreen.getContext('2d');
			} catch {
				offscreen = document.createElement('canvas');
				offscreen.width = BUFFER_SIZE;
				offscreen.height = BUFFER_SIZE;
				offCtx = offscreen.getContext('2d');
			}
		}
		if (!offCtx) return;

		offCtx.clearRect(0, 0, BUFFER_SIZE, BUFFER_SIZE);

		// Group by palette index
		// eslint-disable-next-line svelte/prefer-svelte-reactivity
		const groups = new Map<number, number[]>(); // Local procedural Map; not reactive state.
		const hl = highlightedGroup;

		for (let i = 0; i < pointCount; i++) {
			const g = groupPerPoint[i];
			let arr = groups.get(g);
			if (!arr) {
				arr = [];
				groups.set(g, arr);
			}
			arr.push(i);
		}

		const TAU = Math.PI * 2;
		const r = POINT_RADIUS * (BUFFER_SIZE / 1000);
		const margin = r * 2;
		const usable = BUFFER_SIZE - margin * 2;

		for (const [gIdx, indices] of groups) {
			const dimmed = hl !== null && gIdx !== hl;
			offCtx.globalAlpha = dimmed ? 0.12 : 0.85;
			offCtx.fillStyle = gIdx < palette.length ? palette[gIdx] : '#999999';
			offCtx.beginPath();
			for (const idx of indices) {
				const sx = margin + positions[idx * 2] * usable;
				const sy = margin + (1 - positions[idx * 2 + 1]) * usable;
				offCtx.moveTo(sx + r, sy);
				offCtx.arc(sx, sy, r, 0, TAU);
			}
			offCtx.fill();
		}

		offCtx.globalAlpha = 1;
		bufferDirty = false;
	}

	function drawCanvas2D() {
		if (!canvas || pointCount === 0) return;

		const ctx = canvas.getContext('2d');
		if (!ctx) return;

		const dpr = window.devicePixelRatio || 1;
		const cw = Math.round(width * dpr);
		const ch = Math.round(height * dpr);

		if (canvas.width !== cw || canvas.height !== ch) {
			canvas.width = cw;
			canvas.height = ch;
		}

		ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
		ctx.clearRect(0, 0, width, height);

		if (bufferDirty) renderOffscreen();
		if (!offscreen) return;

		const r = POINT_RADIUS * (BUFFER_SIZE / 1000);
		const margin = r * 2;
		const usable = BUFFER_SIZE - margin * 2;
		const plotW = width - PADDING * 2;
		const plotH = height - PADDING * 2;

		const dw = plotW * scale * (BUFFER_SIZE / usable);
		const dh = plotH * scale * (BUFFER_SIZE / usable);
		const dx = PADDING + offsetX - (margin / usable) * plotW * scale;
		const dy = PADDING + offsetY - (margin / usable) * plotH * scale;

		ctx.imageSmoothingEnabled = true;
		ctx.imageSmoothingQuality = 'high';
		ctx.drawImage(offscreen as CanvasImageSource, 0, 0, BUFFER_SIZE, BUFFER_SIZE, dx, dy, dw, dh);
	}

	// ═══════════════════════════════════════════════════
	// Draw dispatch
	// ═══════════════════════════════════════════════════

	let rafId = 0;

	function scheduleDraw() {
		if (rafId) return;
		rafId = requestAnimationFrame(() => {
			rafId = 0;
			if (useWebGL) drawWebGL();
			else drawCanvas2D();
		});
	}

	// ═══════════════════════════════════════════════════
	// Reactive effects
	// ═══════════════════════════════════════════════════

	// Init renderer
	$effect(() => {
		if (!canvas || rendererReady) return;
		if (initWebGL(canvas)) {
			useWebGL = true;
			rendererReady = true;
		} else {
			useWebGL = false;
			rendererReady = true;
		}
	});

	// Upload positions when they change
	$effect(() => {
		if (!rendererReady || pointCount === 0) return;
		const _p = positions; // dep
		if (useWebGL) uploadGLPositions();
		scheduleDraw();
	});

	// Upload colors when colorBy/highlight/palette changes
	$effect(() => {
		if (!rendererReady || pointCount === 0) return;
		const _g = groupPerPoint; // dep
		const _pal = palette; // dep
		const _hl = highlightedGroup; // dep
		parsedPalette = parsePalette(palette);
		if (useWebGL) {
			uploadGLColors();
		} else {
			bufferDirty = true;
		}
		scheduleDraw();
	});

	// Redraw on view changes
	$effect(() => {
		const _s = scale;
		const _ox = offsetX;
		const _oy = offsetY;
		const _w = width;
		const _h = height;
		const _c = canvas;
		scheduleDraw();
	});

	// Size is tracked reactively via useResizeObserver above

	// ═══════════════════════════════════════════════════
	// Hit testing (spatial grid on Float32Array)
	// ═══════════════════════════════════════════════════

	const GRID_CELLS = 64;
	const grid = $derived.by(() => {
		if (pointCount === 0) return [];
		const cells: number[][] = new Array(GRID_CELLS * GRID_CELLS);
		for (let i = 0; i < cells.length; i++) cells[i] = [];
		for (let i = 0; i < pointCount; i++) {
			const x = positions[i * 2];
			const y = positions[i * 2 + 1];
			const gx = Math.min(GRID_CELLS - 1, Math.max(0, Math.floor(x * GRID_CELLS)));
			const gy = Math.min(GRID_CELLS - 1, Math.max(0, Math.floor(y * GRID_CELLS)));
			cells[gy * GRID_CELLS + gx].push(i);
		}
		return cells;
	});

	function findPointAt(mouseX: number, mouseY: number): number | null {
		if (grid.length === 0) return null;
		const hitRadius = Math.max(5, 3 * scale + 2);
		const plotW = width - PADDING * 2;
		const plotH = height - PADDING * 2;
		const sW = plotW * scale;
		const sH = plotH * scale;
		const ox = offsetX + PADDING;
		const oy = offsetY + PADDING;

		const dx = (mouseX - ox) / sW;
		const dy = 1 - (mouseY - oy) / sH;
		const dataRadius = hitRadius / Math.min(sW, sH);

		const gxMin = Math.max(0, Math.floor((dx - dataRadius) * GRID_CELLS));
		const gxMax = Math.min(GRID_CELLS - 1, Math.floor((dx + dataRadius) * GRID_CELLS));
		const gyMin = Math.max(0, Math.floor((dy - dataRadius) * GRID_CELLS));
		const gyMax = Math.min(GRID_CELLS - 1, Math.floor((dy + dataRadius) * GRID_CELLS));

		let closestIdx: number | null = null;
		let closestDist = hitRadius * hitRadius;

		for (let gy = gyMin; gy <= gyMax; gy++) {
			for (let gx = gxMin; gx <= gxMax; gx++) {
				const cell = grid[gy * GRID_CELLS + gx];
				for (const idx of cell) {
					const px = positions[idx * 2];
					const py = positions[idx * 2 + 1];
					const sx = px * sW + ox;
					const sy = (1 - py) * sH + oy;
					const ddx = mouseX - sx;
					const ddy = mouseY - sy;
					const dist = ddx * ddx + ddy * ddy;
					if (dist < closestDist) {
						closestDist = dist;
						closestIdx = idx;
					}
				}
			}
		}
		return closestIdx;
	}

	// ═══════════════════════════════════════════════════
	// Event handlers
	// ═══════════════════════════════════════════════════

	function handleWheel(e: WheelEvent) {
		e.preventDefault();
		const rect = canvas!.getBoundingClientRect();
		const mouseX = e.clientX - rect.left;
		const mouseY = e.clientY - rect.top;

		const zoomFactor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
		const newScale = Math.max(0.5, Math.min(20, scale * zoomFactor));

		const plotW = width - PADDING * 2;
		const plotH = height - PADDING * 2;
		offsetX =
			mouseX - PADDING - ((mouseX - PADDING - offsetX) / (plotW * scale)) * plotW * newScale;
		offsetY =
			mouseY - PADDING - ((mouseY - PADDING - offsetY) / (plotH * scale)) * plotH * newScale;
		scale = newScale;
	}

	function handleMouseDown(e: MouseEvent) {
		if (e.button === 0) {
			isPanning = true;
			panStartX = e.clientX - offsetX;
			panStartY = e.clientY - offsetY;
		}
	}

	function handleMouseMove(e: MouseEvent) {
		if (isPanning) {
			offsetX = e.clientX - panStartX;
			offsetY = e.clientY - panStartY;
			return;
		}
		const rect = canvas!.getBoundingClientRect();
		const idx = findPointAt(e.clientX - rect.left, e.clientY - rect.top);
		onPointHover(idx, e.clientX, e.clientY);
	}

	function handleMouseUp() {
		isPanning = false;
	}

	function handleMouseLeave() {
		isPanning = false;
		onPointHover(null, 0, 0);
	}

	function handleClick(e: MouseEvent) {
		const rect = canvas!.getBoundingClientRect();
		const idx = findPointAt(e.clientX - rect.left, e.clientY - rect.top);
		onPointClick(idx);
	}

	export function resetView() {
		scale = 1;
		offsetX = 0;
		offsetY = 0;
	}

	export function zoomIn() {
		const cx = width / 2;
		const cy = height / 2;
		const plotW = width - PADDING * 2;
		const plotH = height - PADDING * 2;
		const newScale = Math.min(20, scale * 1.3);
		offsetX = cx - PADDING - ((cx - PADDING - offsetX) / (plotW * scale)) * plotW * newScale;
		offsetY = cy - PADDING - ((cy - PADDING - offsetY) / (plotH * scale)) * plotH * newScale;
		scale = newScale;
	}

	export function zoomOut() {
		const cx = width / 2;
		const cy = height / 2;
		const plotW = width - PADDING * 2;
		const plotH = height - PADDING * 2;
		const newScale = Math.max(0.5, scale / 1.3);
		offsetX = cx - PADDING - ((cx - PADDING - offsetX) / (plotW * scale)) * plotW * newScale;
		offsetY = cy - PADDING - ((cy - PADDING - offsetY) / (plotH * scale)) * plotH * newScale;
		scale = newScale;
	}
</script>

<div
	bind:this={container}
	class="h-full w-full"
	role="img"
	aria-label={t('semantic_map.canvas_aria')}
>
	<canvas
		bind:this={canvas}
		class="h-full w-full cursor-grab active:cursor-grabbing"
		style="width: {width}px; height: {height}px;"
		onwheel={handleWheel}
		onmousedown={handleMouseDown}
		onmousemove={handleMouseMove}
		onmouseup={handleMouseUp}
		onmouseleave={handleMouseLeave}
		onclick={handleClick}
	></canvas>
</div>
