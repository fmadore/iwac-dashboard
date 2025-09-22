import { writable, derived } from 'svelte/store';

export type Language = 'en' | 'fr';

export const translations = {
	en: {
		'app.title': 'IWAC Database Overview',
		'nav.overview': 'Overview',
		'nav.countries': 'Countries',
		'nav.languages': 'Languages',
		'nav.timeline': 'Timeline',
		'nav.index': 'Index',
		'nav.categories': 'Categories',
		'nav.words': 'Word Analysis',
		'stats.total_items': 'Total Items',
		'stats.total_items_desc': 'Documents in database',
		'stats.countries': 'Countries',
		'stats.countries_desc': 'Different countries represented',
		'stats.languages': 'Languages',
		'stats.languages_desc': 'Different languages available',
		'stats.types': 'Document Types',
		'stats.types_desc': 'Various document categories',
		'chart.recent_additions': 'Recent Additions',
		'chart.top_countries': 'Top Countries',
		'chart.language_distribution': 'Language Distribution',
		'chart.language_distribution_desc': 'Documents by language',
		'chart.percentage': 'Percentage',
		'chart.documents': 'Documents',
		'chart.no_data': 'No data available',
		'common.loading': 'Loading...',
		'common.error': 'Error loading data',
		'common.search': 'Search...',
		'common.export': 'Export',
		'common.filter': 'Filter',
		'common.reset': 'Reset',
		'table.search_placeholder': 'Search title, type, or country...',
		'table.rows_count': '{0} rows',
		'table.no_results': 'No results',
		'table.load_error': 'Failed to load entities',
		'table.title': 'Title',
		'table.type': 'Type',
		'table.frequency': 'Frequency',
		'table.first': 'First occurrence',
		'table.last': 'Last occurrence',
		'table.countries': 'Countries'
	},
	fr: {
		'app.title': 'Aperçu de la base de données IWAC',
		'nav.overview': 'Vue d\'ensemble',
		'nav.countries': 'Pays',
		'nav.languages': 'Langues',
		'nav.timeline': 'Chronologie',
		'nav.index': 'Index',
		'nav.categories': 'Catégories',
		'nav.words': 'Analyse des mots',
		'stats.total_items': 'Total des éléments',
		'stats.total_items_desc': 'Documents dans la base de données',
		'stats.countries': 'Pays',
		'stats.countries_desc': 'Différents pays représentés',
		'stats.languages': 'Langues',
		'stats.languages_desc': 'Différentes langues disponibles',
		'stats.types': 'Types de documents',
		'stats.types_desc': 'Diverses catégories de documents',
		'chart.recent_additions': 'Ajouts récents',
		'chart.top_countries': 'Principaux pays',
		'chart.language_distribution': 'Distribution des langues',
		'chart.language_distribution_desc': 'Documents par langue',
		'chart.percentage': 'Pourcentage',
		'chart.documents': 'Documents',
		'chart.no_data': 'Aucune donnees disponibles',
		'common.loading': 'Chargement...',
		'common.error': 'Erreur lors du chargement des données',
		'common.search': 'Rechercher...',
		'common.export': 'Exporter',
		'common.filter': 'Filtrer',
		'common.reset': 'Réinitialiser',
		'table.search_placeholder': 'Rechercher un titre, un type ou un pays...',
		'table.rows_count': '{0} lignes',
		'table.no_results': 'Aucun résultat',
		'table.load_error': 'Échec du chargement des entités',
		'table.title': 'Titre',
		'table.type': 'Type',
		'table.frequency': 'Fréquence',
		'table.first': 'Première occurrence',
		'table.last': 'Dernière occurrence',
		'table.countries': 'Pays'
	}
} as const;

export const languageStore = writable<Language>('en');

export const t = derived(languageStore, ($lang) => {
	return (key: string, params: any[] = []) => {
		const translation = translations[$lang]?.[key as keyof typeof translations[typeof $lang]] || key;
		return params.reduce((str, param, i) => str.replace(`{${i}}`, param), translation);
	};
});


