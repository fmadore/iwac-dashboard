<script lang="ts">
	import LayerChartPieChart from './LayerChartPieChart.svelte';

	// Backwards-compatible wrapper: this component used to be the ECharts implementation.
	// Keeping it as an alias avoids breaking any older imports.
	const props = $props();
</script>

<LayerChartPieChart {...props} />
