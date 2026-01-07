<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Slider } from '$lib/components/ui/slider/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import type { NodeSizeBy, NetworkViewMode } from '$lib/types/network.js';
	import { ZoomIn, ZoomOut, Maximize2, Map, Network } from '@lucide/svelte';

	interface Props {
		viewMode: NetworkViewMode;
		nodeSizeBy: NodeSizeBy;
		minEdgeWeight: number;
		maxEdgeWeight: number;
		onViewModeChange: (mode: NetworkViewMode) => void;
		onNodeSizeByChange: (sizeBy: NodeSizeBy) => void;
		onMinEdgeWeightChange: (weight: number) => void;
		onZoomIn: () => void;
		onZoomOut: () => void;
		onResetCamera: () => void;
	}

	let {
		viewMode,
		nodeSizeBy,
		minEdgeWeight,
		maxEdgeWeight,
		onViewModeChange,
		onNodeSizeByChange,
		onMinEdgeWeightChange,
		onZoomIn,
		onZoomOut,
		onResetCamera
	}: Props = $props();

	const nodeSizeOptions: { value: NodeSizeBy; label: string }[] = [
		{ value: 'count', label: 'network.size_by_count' },
		{ value: 'degree', label: 'network.size_by_degree' },
		{ value: 'strength', label: 'network.size_by_strength' }
	];

	function handleNodeSizeChange(value: string | undefined) {
		if (value) {
			onNodeSizeByChange(value as NodeSizeBy);
		}
	}

	function handleSliderChange(value: number) {
		onMinEdgeWeightChange(value);
	}
</script>

<div class="flex flex-wrap items-center gap-4">
	<!-- View Mode Toggle -->
	<div class="flex items-center gap-2">
		<Label class="text-sm font-medium">{t('network.view_mode')}:</Label>
		<div class="flex rounded-lg border bg-muted p-1">
			<Button
				variant={viewMode === 'graph' ? 'default' : 'ghost'}
				size="sm"
				class="h-8 px-3"
				onclick={() => onViewModeChange('graph')}
			>
				<Network class="mr-1 h-4 w-4" />
				{t('network.graph_view')}
			</Button>
			<Button
				variant={viewMode === 'map' ? 'default' : 'ghost'}
				size="sm"
				class="h-8 px-3"
				onclick={() => onViewModeChange('map')}
			>
				<Map class="mr-1 h-4 w-4" />
				{t('network.map_view')}
			</Button>
		</div>
	</div>

	<!-- Node Size Selector -->
	<div class="flex items-center gap-2">
		<Label class="text-sm font-medium">{t('network.node_size')}:</Label>
		<Select.Root type="single" value={nodeSizeBy} onValueChange={handleNodeSizeChange}>
			<Select.Trigger class="w-40">
				{t(nodeSizeOptions.find((o) => o.value === nodeSizeBy)?.label || '')}
			</Select.Trigger>
			<Select.Content>
				{#each nodeSizeOptions as option (option.value)}
					<Select.Item value={option.value}>{t(option.label)}</Select.Item>
				{/each}
			</Select.Content>
		</Select.Root>
	</div>

	<!-- Edge Weight Filter -->
	<div class="flex items-center gap-2">
		<Label class="text-sm font-medium">{t('network.min_edge_weight')}:</Label>
		<div class="flex w-35 items-center gap-2">
			<Slider
				type="single"
				value={minEdgeWeight}
				min={1}
				max={maxEdgeWeight}
				step={1}
				onValueChange={handleSliderChange}
				class="flex-1"
			/>
			<span class="w-8 text-right text-sm text-muted-foreground">{minEdgeWeight}</span>
		</div>
	</div>

	<!-- Zoom Controls -->
	<div class="ml-auto flex items-center gap-1">
		<Button variant="outline" size="icon" onclick={onZoomIn} title={t('network.zoom_in')}>
			<ZoomIn class="h-4 w-4" />
		</Button>
		<Button variant="outline" size="icon" onclick={onZoomOut} title={t('network.zoom_out')}>
			<ZoomOut class="h-4 w-4" />
		</Button>
		<Button variant="outline" size="icon" onclick={onResetCamera} title={t('network.reset_view')}>
			<Maximize2 class="h-4 w-4" />
		</Button>
	</div>
</div>
