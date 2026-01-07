<script lang="ts">
	import { mapDataStore } from '$lib/stores/mapDataStore.svelte.js';
	import { t } from '$lib/stores/translationStore.svelte.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Slider } from '$lib/components/ui/slider/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { RotateCcw, Globe, Calendar } from '@lucide/svelte';

	// Reactive state from store
	const availableSourceCountries = $derived(mapDataStore.availableSourceCountries);
	const yearRange = $derived(mapDataStore.yearRange);
	const selectedSourceCountry = $derived(mapDataStore.selectedSourceCountry);
	const selectedYearRange = $derived(mapDataStore.selectedYearRange);

	// Local state for slider
	let sliderValue = $state<number[]>([]);

	// Initialize slider when year range becomes available
	$effect(() => {
		if (yearRange && sliderValue.length === 0) {
			sliderValue = [yearRange.min, yearRange.max];
		}
	});

	// Sync slider with store when selectedYearRange changes externally
	$effect(() => {
		if (yearRange) {
			if (selectedYearRange) {
				sliderValue = [selectedYearRange[0], selectedYearRange[1]];
			} else {
				sliderValue = [yearRange.min, yearRange.max];
			}
		}
	});

	function handleCountryChange(value: string | undefined) {
		if (value === 'all' || !value) {
			mapDataStore.setSelectedSourceCountry(null);
		} else {
			mapDataStore.setSelectedSourceCountry(value);
		}
	}

	function handleYearSliderChange(newValue: number[]) {
		if (newValue.length >= 2 && yearRange) {
			// Only update if it's different from full range
			if (newValue[0] === yearRange.min && newValue[1] === yearRange.max) {
				mapDataStore.setSelectedYearRange(null);
			} else {
				mapDataStore.setSelectedYearRange([newValue[0], newValue[1]]);
			}
		}
	}

	function handleResetFilters() {
		mapDataStore.resetFilters();
		if (yearRange) {
			sliderValue = [yearRange.min, yearRange.max];
		}
	}

	const hasActiveFilters = $derived(
		selectedSourceCountry !== null || selectedYearRange !== null
	);

	// Format year range display
	const yearRangeDisplay = $derived(() => {
		if (sliderValue.length >= 2) {
			return `${sliderValue[0]} - ${sliderValue[1]}`;
		}
		return '';
	});
</script>

<div class="map-filters flex flex-wrap items-center gap-4">
	<!-- Country Picker -->
	<div class="filter-group flex items-center gap-2">
		<Globe size={16} class="text-muted-foreground" />
		<Select.Root 
			type="single"
			value={selectedSourceCountry ?? 'all'}
			onValueChange={handleCountryChange}
		>
			<Select.Trigger class="w-45">
				{selectedSourceCountry ?? t('worldmap.filter.all_countries')}
			</Select.Trigger>
			<Select.Content>
				<Select.Item value="all">{t('worldmap.filter.all_countries')}</Select.Item>
				<Select.Separator />
				{#each availableSourceCountries as country}
					<Select.Item value={country}>{country}</Select.Item>
				{/each}
			</Select.Content>
		</Select.Root>
	</div>

	<!-- Year Slider -->
	{#if yearRange}
		<div class="filter-group flex items-center gap-3">
			<Calendar size={16} class="text-muted-foreground" />
			<div class="flex flex-col gap-1">
				<div class="flex items-center gap-2">
					<Slider
						type="multiple"
						value={sliderValue}
						onValueChange={handleYearSliderChange}
						min={yearRange.min}
						max={yearRange.max}
						step={1}
						class="w-50"
					/>
					<span class="text-sm text-muted-foreground whitespace-nowrap min-w-22.5">
						{yearRangeDisplay()}
					</span>
				</div>
			</div>
		</div>
	{/if}

	<!-- Reset Button -->
	{#if hasActiveFilters}
		<Button
			variant="ghost"
			size="sm"
			onclick={handleResetFilters}
			class="gap-1"
		>
			<RotateCcw size={14} />
			{t('worldmap.filter.reset')}
		</Button>
	{/if}
</div>

<style>
	.map-filters {
		padding: 0.5rem;
	}

	.filter-group {
		background: var(--card);
		padding: 0.5rem 0.75rem;
		border-radius: 0.5rem;
		border: 1px solid var(--border);
	}
</style>
