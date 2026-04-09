<script lang="ts">
	import { resolve } from '$app/paths';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import {
		BarChart3,
		Globe2,
		Languages,
		Calendar,
		FileType,
		Tag,
		BookOpen,
		Home,
		BookMarked,
		User,
		BrainCircuit,
		Grid3X3,
		MapPin,
		Newspaper,
		Network,
		Share2,
		CalendarRange,
		UserCircle,
		Hash,
		Building2,
		Users,
		TreePine,
		Waypoints,
		GitFork,
		ChartScatter
	} from '@lucide/svelte';
	import { page } from '$app/state';
	import { t } from '$lib/stores/translationStore.svelte.js';

	const overviewItems = [
		{ href: resolve('/'), icon: Home, label: 'nav.overview' },
		{ href: resolve('/countries'), icon: Globe2, label: 'nav.countries' },
		{ href: resolve('/languages'), icon: Languages, label: 'nav.languages' },
		{ href: resolve('/newspaper-coverage'), icon: CalendarRange, label: 'nav.newspaper_coverage' },
		{ href: resolve('/timeline'), icon: Calendar, label: 'nav.timeline' },
		{ href: resolve('/entities'), icon: FileType, label: 'nav.entities' },
		{ href: resolve('/categories'), icon: Tag, label: 'nav.categories' }
	];

	const referencesItems = [
		{ href: resolve('/references/by-year'), icon: BookMarked, label: 'nav.references_by_year' },
		{ href: resolve('/references/treemap'), icon: TreePine, label: 'nav.treemap' },
		{ href: resolve('/references/authors'), icon: User, label: 'nav.top_authors' },
		{ href: resolve('/references/publishers'), icon: Building2, label: 'nav.publishers' },
		{ href: resolve('/references/coauthor-network'), icon: Users, label: 'nav.coauthor_network' },
		{
			href: resolve('/references/subject-cooccurrence'),
			icon: Waypoints,
			label: 'nav.subject_cooccurrence'
		},
		{ href: resolve('/references/provenance-map'), icon: MapPin, label: 'nav.provenance_map' }
	];

	const textualAnalysisItems = [
		{ href: resolve('/words'), icon: BookOpen, label: 'nav.words' },
		{ href: resolve('/keywords'), icon: Hash, label: 'nav.keywords' },
		{ href: resolve('/scary'), icon: BarChart3, label: 'nav.scary_words' },
		{ href: resolve('/cooccurrence'), icon: Grid3X3, label: 'nav.cooccurrence' },
		{ href: resolve('/topics'), icon: BrainCircuit, label: 'nav.topics' },
		{ href: resolve('/topic-network'), icon: Network, label: 'nav.topic_network' },
		{ href: resolve('/semantic-map'), icon: ChartScatter, label: 'nav.semantic_map' }
	];

	const spatialAnalysisItems = [
		{ href: resolve('/spatial/world-map'), icon: MapPin, label: 'nav.world_map' },
		{ href: resolve('/spatial/sources'), icon: Newspaper, label: 'nav.sources' },
		{ href: resolve('/entity-spatial'), icon: UserCircle, label: 'nav.entity_spatial' }
	];

	const networkAnalysisItems = [
		{ href: resolve('/network'), icon: Share2, label: 'nav.network' },
		{ href: resolve('/network-map'), icon: Network, label: 'nav.network_map' },
		{ href: resolve('/knowledge-graph'), icon: GitFork, label: 'nav.knowledge_graph' }
	];
</script>

<Sidebar.Root collapsible="offcanvas">
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg">
					<div
						class="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground"
					>
						<span class="text-lg font-bold">IW</span>
					</div>
					<div class="grid flex-1 text-left text-sm leading-tight">
						<span class="truncate font-semibold">{t('app.title')}</span>
						<span class="truncate text-xs text-sidebar-foreground/70">{t('app.subtitle')}</span>
					</div>
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Header>
	<Sidebar.Content class="!flex-initial">
		<Sidebar.Group>
			<Sidebar.GroupLabel>{t('nav.overview')}</Sidebar.GroupLabel>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each overviewItems as item (item.href)}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton isActive={page.url.pathname === item.href}>
								{#snippet child({ props })}
									<!-- eslint-disable svelte/no-navigation-without-resolve -- item.href is built via resolve() above. -->
									<a href={item.href} {...props}>
										<item.icon class="h-4 w-4" />
										<span>{t(item.label)}</span>
									</a>
									<!-- eslint-enable svelte/no-navigation-without-resolve -->
								{/snippet}
							</Sidebar.MenuButton>
						</Sidebar.MenuItem>
					{/each}
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>
		<Sidebar.Group>
			<Sidebar.GroupLabel>{t('nav.references')}</Sidebar.GroupLabel>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each referencesItems as item (item.href)}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton isActive={page.url.pathname === item.href}>
								{#snippet child({ props })}
									<!-- eslint-disable svelte/no-navigation-without-resolve -- item.href is built via resolve() above. -->
									<a href={item.href} {...props}>
										<item.icon class="h-4 w-4" />
										<span>{t(item.label)}</span>
									</a>
									<!-- eslint-enable svelte/no-navigation-without-resolve -->
								{/snippet}
							</Sidebar.MenuButton>
						</Sidebar.MenuItem>
					{/each}
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>
		<Sidebar.Group>
			<Sidebar.GroupLabel>{t('nav.textual_analysis')}</Sidebar.GroupLabel>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each textualAnalysisItems as item (item.href)}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton isActive={page.url.pathname === item.href}>
								{#snippet child({ props })}
									<!-- eslint-disable svelte/no-navigation-without-resolve -- item.href is built via resolve() above. -->
									<a href={item.href} {...props}>
										<item.icon class="h-4 w-4" />
										<span>{t(item.label)}</span>
									</a>
									<!-- eslint-enable svelte/no-navigation-without-resolve -->
								{/snippet}
							</Sidebar.MenuButton>
						</Sidebar.MenuItem>
					{/each}
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>
		<Sidebar.Group>
			<Sidebar.GroupLabel>{t('nav.spatial_analysis')}</Sidebar.GroupLabel>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each spatialAnalysisItems as item (item.href)}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton isActive={page.url.pathname === item.href}>
								{#snippet child({ props })}
									<!-- eslint-disable svelte/no-navigation-without-resolve -- item.href is built via resolve() above. -->
									<a href={item.href} {...props}>
										<item.icon class="h-4 w-4" />
										<span>{t(item.label)}</span>
									</a>
									<!-- eslint-enable svelte/no-navigation-without-resolve -->
								{/snippet}
							</Sidebar.MenuButton>
						</Sidebar.MenuItem>
					{/each}
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>
		<Sidebar.Group>
			<Sidebar.GroupLabel>{t('nav.network_analysis')}</Sidebar.GroupLabel>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each networkAnalysisItems as item (item.href)}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton isActive={page.url.pathname === item.href}>
								{#snippet child({ props })}
									<!-- eslint-disable svelte/no-navigation-without-resolve -- item.href is built via resolve() above. -->
									<a href={item.href} {...props}>
										<item.icon class="h-4 w-4" />
										<span>{t(item.label)}</span>
									</a>
									<!-- eslint-enable svelte/no-navigation-without-resolve -->
								{/snippet}
							</Sidebar.MenuButton>
						</Sidebar.MenuItem>
					{/each}
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>
	</Sidebar.Content>
	<Sidebar.Rail />
</Sidebar.Root>
