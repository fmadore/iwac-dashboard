<script lang="ts">
  import { onMount } from 'svelte';
  import { base } from '$app/paths';
  import { Card } from '$lib/components/ui/card/index.js';
  import EntitiesTable from './entities-table.svelte';
  import EChartsBarChart from '$lib/components/charts/EChartsBarChart.svelte';
  import { t, languageStore } from '$lib/stores/translationStore.svelte.js';

  type ApiChartData = { labels?: string[]; values?: number[] };
  type ChartDataItem = { category: string; documents: number; originalKey: string };

  let rawChartData = $state<{ category: string; documents: number }[]>([]);
  let isLoading = $state(true);
  let fetchError = $state<string | null>(null);

  // Map English entity names to translation keys
  const entityTranslationMap: Record<string, string> = {
    'Authority Files': 'entity.authority files',
    'Events': 'entity.events',
    'Locations': 'entity.locations',
    'Organizations': 'entity.organizations',
    'Persons': 'entity.persons',
    'Topics': 'entity.topics'
  };

  // Reactive chart data that updates with language changes
  const chartData = $derived.by(() => {
    // Access languageStore to make this reactive
    const currentLang = languageStore.current;
    
    const translated = rawChartData.map(item => ({
      category: entityTranslationMap[item.category] ? t(entityTranslationMap[item.category]) : item.category,
      documents: item.documents,
      originalKey: item.category // Keep original for color mapping
    }));
    
    console.log('🌐 ChartData Derived', {
      currentLang,
      rawData: rawChartData.map(d => d.category),
      translatedData: translated.map(d => d.category)
    });
    
    return translated;
  });

  const totalIndexItems = $derived.by(() =>
    rawChartData.reduce((sum, item) => sum + item.documents, 0)
  );

  const totalIndexItemsLabel = $derived.by(() => {
    const currentLang = languageStore.current;
    const locale = currentLang === 'fr' ? 'fr-FR' : 'en-US';
    return totalIndexItems.toLocaleString(locale);
  });

  async function loadChartData() {
    try {
      const response = await fetch(`${base}/data/index-types.json`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);

      const payload = (await response.json()) as ApiChartData;
      const labels = payload.labels ?? [];
      const values = payload.values ?? [];

      rawChartData = labels.map((category, index) => ({
        category,
        documents: values[index] ?? 0
      }));
      fetchError = null;
    } catch (error) {
      console.error('Failed to load index-types.json', error);
      fetchError = t('common.error');
      rawChartData = [];
    } finally {
      isLoading = false;
    }
  }

  onMount(() => {
    loadChartData();
  });
</script>

<div class="space-y-6">
  <div>
    <h2 class="text-3xl font-bold tracking-tight">{t('nav.entities')}</h2>
    <p class="text-muted-foreground">{t('index.top_entity_types_subtitle', [totalIndexItemsLabel])}</p>
  </div>

  <Card class="p-4">
    {#if isLoading}
      <div class="grid h-96 place-items-center text-sm text-muted-foreground">
        {t('common.loading')}
      </div>
    {:else if fetchError}
      <div class="grid h-96 place-items-center text-sm text-destructive">
        {fetchError}
      </div>
    {:else if !chartData.length}
      <div class="grid h-96 place-items-center text-sm text-muted-foreground">
        {t('chart.no_data')}
      </div>
    {:else}
      <div class="w-full h-96">
        <EChartsBarChart 
          data={chartData}
          height={384}
          animationDuration={750}
          useMultipleColors={true}
        />
      </div>
    {/if}
  </Card>

  <EntitiesTable />
</div>
