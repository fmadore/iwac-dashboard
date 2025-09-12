<script lang="ts">
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
	import { page } from '$app/stores';
	import { t } from '$lib/stores/translationStore.js';

	const navItems = [
		{ href: '/', icon: Home, label: 'nav.overview' },
		{ href: '/countries', icon: Globe2, label: 'nav.countries' },
		{ href: '/languages', icon: Languages, label: 'nav.languages' },
		{ href: '/timeline', icon: Calendar, label: 'nav.timeline' },
		{ href: '/types', icon: FileType, label: 'nav.types' },
		{ href: '/categories', icon: Tag, label: 'nav.categories' },
		{ href: '/words', icon: BookOpen, label: 'nav.words' }
	];
</script>

<Sidebar.Root>
	<Sidebar.Content>
		<Sidebar.Group>
			<Sidebar.GroupLabel>Navigation</Sidebar.GroupLabel>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each navItems as item}
						<Sidebar.MenuItem>
							<a href={item.href} class="block w-full">
								<Sidebar.MenuButton isActive={$page.url.pathname === item.href}>
									<svelte:component this={item.icon} class="w-4 h-4" />
									<span>{$t(item.label)}</span>
								</Sidebar.MenuButton>
							</a>
						</Sidebar.MenuItem>
					{/each}
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>
	</Sidebar.Content>
</Sidebar.Root>
