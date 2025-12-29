import { base } from '$app/paths';

const site = 'https://fmadore.github.io';
const pages = [
	'',
	'/countries',
	'/languages',
	'/timeline',
	'/entities',
	'/categories',
	'/references/by-year',
	'/references/authors',
	'/words',
	'/scary',
	'/cooccurrence',
	'/topics',
	'/spatial/world-map',
	'/spatial/sources'
];

/** @type {import('./$types.js').RequestHandler} */
export async function GET() {
	const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${pages
			.map(
				(page) => `	<url>
		<loc>${site}${base}${page}</loc>
		<changefreq>weekly</changefreq>
		<priority>${page === '' ? '1.0' : '0.8'}</priority>
	</url>`
			)
			.join('\n')}
</urlset>`.trim();

	return new Response(sitemap, {
		headers: {
			'Content-Type': 'application/xml',
			'Cache-Control': 'max-age=0, s-maxage=3600'
		}
	});
}

export const prerender = true;
