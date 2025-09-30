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
		Home
	} from '@lucide/svelte';
	import { page } from '$app/state';
	import { t } from '$lib/stores/translationStore.svelte.js';

	const navItems = [
		{ href: `${base}/`, icon: Home, label: 'nav.overview' },
		{ href: `${base}/countries`, icon: Globe2, label: 'nav.countries' },
		{ href: `${base}/languages`, icon: Languages, label: 'nav.languages' },
		{ href: `${base}/timeline`, icon: Calendar, label: 'nav.timeline' },
		{ href: `${base}/entities`, icon: FileType, label: 'nav.entities' },
		{ href: `${base}/categories`, icon: Tag, label: 'nav.categories' },
		{ href: `${base}/words`, icon: BookOpen, label: 'nav.words' }
	];
</script>

<Sidebar.Root collapsible="offcanvas">
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg">
					<div class="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
						<span class="text-lg font-bold">IW</span>
					</div>
					<div class="grid flex-1 text-left text-sm leading-tight">
						<span class="truncate font-semibold">{t('app.title')}</span>
						<span class="truncate text-xs">{t('app.subtitle')}</span>
					</div>
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Header>
	<Sidebar.Content>
		<Sidebar.Group>
			<Sidebar.GroupLabel>Navigation</Sidebar.GroupLabel>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each navItems as item}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton isActive={page.url.pathname === item.href}>
								{#snippet child({ props })}
									<a href={item.href} {...props}>
										<item.icon class="w-4 h-4" />
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
