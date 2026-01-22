import tailwindcss from '@tailwindcss/vite';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import { SvelteKitPWA } from '@vite-pwa/sveltekit';

export default defineConfig(({ mode }) => {
	const isDev = mode === 'development';
	const base = isDev ? '' : '/iwac-dashboard';

	return {
		plugins: [
			tailwindcss(),
			sveltekit(),
			SvelteKitPWA({
				registerType: 'autoUpdate',
				injectRegister: 'auto',
				includeAssets: ['apple-touch-icon.png', 'Logo ZMO.png'],
				manifest: {
					name: 'IWAC Dashboard',
					short_name: 'IWAC DB',
					description:
						'Islam West Africa Collection - Database visualization and analytics dashboard',
					theme_color: '#ffffff',
					background_color: '#ffffff',
					display: 'standalone',
					scope: base ? `${base}/` : '/',
					start_url: base ? `${base}/` : '/',
					icons: [
						{
							src: 'pwa-192x192.png',
							sizes: '192x192',
							type: 'image/png'
						},
						{
							src: 'pwa-512x512.png',
							sizes: '512x512',
							type: 'image/png'
						},
						{
							src: 'pwa-512x512.png',
							sizes: '512x512',
							type: 'image/png',
							purpose: 'any maskable'
						}
					]
				},
				workbox: {
					// Cache static assets
					globPatterns: ['**/*.{js,css,html,ico,png,svg,webmanifest}'],
					// Increase limit for large files (keywords page ~12.6MB, JSON data files ~6MB)
					maximumFileSizeToCacheInBytes: 15 * 1024 * 1024, // 15 MiB
					// Cache JSON data files
					runtimeCaching: [
						{
							urlPattern: /^.*\/data\/.*\.json$/,
							handler: 'CacheFirst',
							options: {
								cacheName: 'iwac-data-cache',
								expiration: {
									maxEntries: 100,
									maxAgeSeconds: 60 * 60 * 24 * 7 // 7 days
								}
							}
						}
					],
					// SvelteKit adapter-static prerender caches the app shell as `/` (not `/index.html`).
					// When deployed under a subpath (e.g. GitHub Pages), the SW scope already applies the base.
					// Using `${base}/index.html` here causes Workbox to look for a non-precached URL.
					navigateFallback: base ? `${base}/` : '/',
					navigateFallbackAllowlist: [/^(?!\/__)/],
					cleanupOutdatedCaches: true
				}
			})
		],
		// Pre-bundle dynamically imported dependencies to avoid "Outdated Optimize Dep" errors
		optimizeDeps: {
			include: ['graphology', 'sigma', 'graphology-layout-forceatlas2']
		},
		test: {
			projects: [
				{
					extends: './vite.config.ts',
					test: {
						name: 'client',
						environment: 'browser',
						browser: {
							enabled: true,
							provider: 'playwright',
							instances: [{ browser: 'chromium' }]
						},
						include: ['src/**/*.svelte.{test,spec}.{js,ts}'],
						exclude: ['src/lib/server/**'],
						setupFiles: ['./vitest-setup-client.ts']
					}
				},
				{
					extends: './vite.config.ts',
					test: {
						name: 'server',
						environment: 'node',
						include: ['src/**/*.{test,spec}.{js,ts}'],
						exclude: ['src/**/*.svelte.{test,spec}.{js,ts}']
					}
				}
			]
		}
	};
});
