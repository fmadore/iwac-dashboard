import type { PageLoad } from './$types.js';
import { base } from '$app/paths';

interface PieItem { label: string; value: number; percentage?: number }
interface GlobalLanguageData {
  data: PieItem[];
  total: number;
  languages: number;
  generated_at: string;
}

interface FacetEntry {
  data: PieItem[];
  total: number;
  languages: number;
}

interface FacetsData {
  facets: Record<string, FacetEntry>;
  countries?: string[];
  types?: string[];
  generated_at: string;
}

export const load: PageLoad = async ({ fetch }) => {
  const [globalRes, countriesRes, typesRes] = await Promise.all([
    fetch(`${base}/data/language-global.json`),
    fetch(`${base}/data/language-countries.json`),
    fetch(`${base}/data/language-types.json`)
  ]);

  if (!globalRes.ok) {
    throw new Error('Failed to load language-global.json');
  }

  const global: GlobalLanguageData = await globalRes.json();
  const countries: FacetsData | null = countriesRes.ok ? await countriesRes.json() : null;
  const types: FacetsData | null = typesRes.ok ? await typesRes.json() : null;

  return { global, countries, types };
};
