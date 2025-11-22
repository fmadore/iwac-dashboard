<script lang="ts">
	import { base } from '$app/paths';
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
		User
	} from '@lucide/svelte';
	import { page } from '$app/state';
	import { t } from '$lib/stores/translationStore.svelte.js';

	const overviewItems = [
		{ href: `${base}/`, icon: Home, label: 'nav.overview' },
		{ href: `${base}/countries`, icon: Globe2, label: 'nav.countries' },
		{ href: `${base}/languages`, icon: Languages, label: 'nav.languages' },
		{ href: `${base}/timeline`, icon: Calendar, label: 'nav.timeline' },
		{ href: `${base}/entities`, icon: FileType, label: 'nav.entities' },
		{ href: `${base}/categories`, icon: Tag, label: 'nav.categories' }
	];

	const referencesItems = [
		{ href: `${base}/references/by-year`, icon: BookMarked, label: 'nav.references_by_year' },
		{ href: `${base}/references/authors`, icon: User, label: 'nav.top_authors' }
	];

	const textualAnalysisItems = [
		{ href: `${base}/words`, icon: BookOpen, label: 'nav.words' },
		{ href: `${base}/scary`, icon: BarChart3, label: 'nav.scary_words' }
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
	<Sidebar.Content>
		<Sidebar.Group>
			<Sidebar.GroupLabel>{t('nav.overview')}</Sidebar.GroupLabel>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each overviewItems as item (item.href)}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton isActive={page.url.pathname === item.href}>
								{#snippet child({ props })}
									<a href={item.href} {...props}>
										<item.icon class="h-4 w-4" />
										<span>{t(item.label)}</span>
									</a>
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
									<a href={item.href} {...props}>
										<item.icon class="h-4 w-4" />
										<span>{t(item.label)}</span>
									</a>
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
									<a href={item.href} {...props}>
										<item.icon class="h-4 w-4" />
										<span>{t(item.label)}</span>
									</a>
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
