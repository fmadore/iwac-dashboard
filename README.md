# IWAC Dashboard

An interactive visualization platform for exploring the **Islam West Africa Collection** — a dataset of 19,000+ documents on Islam and Muslims in West Africa.

🌐 **[Access the Dashboard](https://fmadore.github.io/iwac-dashboard/)** | 📊 **[Dataset on Hugging Face](https://huggingface.co/datasets/fmadore/islam-west-africa-collection)**

## What Is This?

The IWAC Dashboard transforms a large scholarly dataset into an accessible, interactive exploration tool. It enables researchers to discover patterns, relationships, and trends across thousands of documents — without writing code or querying databases.

**Designed for:** Scholars in Islamic studies, African studies, religious studies, media studies, digital humanities, and related fields.

**Languages:** Fully bilingual interface (English/French) with real-time switching.

## Geographic & Temporal Coverage

- **Countries:** Côte d'Ivoire, Burkina Faso, Benin, Togo, Niger, Nigeria
- **Time span:** Documents from 1912 to present
- **Document types:** Press articles, academic publications, archival documents, audiovisual materials

---

## Explore the Dashboard

### Overview

The entry point provides key statistics at a glance: total documents, language distribution, country coverage, and recent additions to the collection.

### Geographic Analysis

| Page | What You Can Discover |
|------|----------------------|
| **Country Distribution** | Which West African countries have the most documentation? Interactive treemap showing document density by nation. |
| **World Map** | Geographic spread of the collection visualized on an interactive choropleth map. |
| **Sources Map** | Where are the newspapers and publication sources located? |
| **Entity Geographic Footprint** | Select any person, organization, or topic and see where they appear across the region. Track an imam's influence, an organization's reach, or a concept's geographic spread. |

### Temporal Analysis

| Page | What You Can Discover |
|------|----------------------|
| **Timeline** | How has coverage of Islam in West Africa evolved over time? View growth trajectories, monthly additions, and identify periods of intensive documentation. |
| **Categories Over Time** | How has the composition of document types changed across decades? |
| **References by Year** | Publication patterns and bibliographic trends across time periods. |

### Textual Analysis

| Page | What You Can Discover |
|------|----------------------|
| **Word Cloud & Frequency** | What terms appear most frequently? Filter by country or year to see regional and temporal variations in terminology. |
| **Word Co-occurrence** | Which terms appear together? Identify semantic clusters and conceptual relationships in the literature. |
| **Topic Modeling** | What themes emerge from automated analysis? Browse detected topics and their prevalence. |
| **Sensitive Terms** | Track concerning or problematic terminology over time. Useful for critical discourse analysis and understanding media framing. |

### Network Analysis

| Page | What You Can Discover |
|------|----------------------|
| **Entity Network** | How are people, organizations, places, and topics connected? Interactive graph showing relationships based on co-mentions in documents. |
| **Spatial Network** | Which locations are mentioned together? Geographic clusters and regional connections visualized on a map. |

### Entity & Reference Data

| Page | What You Can Discover |
|------|----------------------|
| **Entity Index** | Searchable directory of all persons, organizations, events, locations, and topics extracted from the collection. |
| **Language Distribution** | What languages are represented? Breakdown by document type and country. |
| **Top Authors** | Who has contributed most to the scholarly literature? Publication counts and activity periods. |

---

## Research Questions You Can Explore

The dashboard helps researchers investigate questions such as:

**Geographic patterns**
- Where is Islamic practice and scholarship most documented in francophone West Africa?
- How does coverage differ between coastal and Sahelian countries?

**Temporal dynamics**
- How has media attention to Islam in West Africa changed since independence?
- What events correlate with spikes in documentation?

**Actors and networks**
- Who are the key religious leaders, scholars, and organizations mentioned?
- How are different actors connected through co-mentions?

**Discourse analysis**
- What terminology characterizes coverage of Islam in this region?
- How do word patterns differ between countries or time periods?
- What potentially problematic framings appear in the sources?

**Entity tracking**
- Where does a specific religious leader appear in the documentary record?
- What is the geographic footprint of a particular Islamic organization?

---

## Features

- **No coding required** — All visualizations are interactive and filterable through the interface
- **Shareable views** — URLs preserve your filters and selections for sharing with colleagues
- **Offline capable** — Works without internet connection after initial load
- **Dark/Light themes** — Choose your preferred display mode
- **Responsive design** — Works on desktop, tablet, and mobile devices
- **Export options** — Download visualizations as SVG files

---

## Data Source

All data comes from the [Islam West Africa Collection](https://huggingface.co/datasets/fmadore/islam-west-africa-collection) on Hugging Face, a curated dataset documenting how francophone West African newspapers have covered Islam and Muslims from the colonial period to the present.

The collection includes:
- **Articles**: Press coverage from major West African newspapers
- **Publications**: Academic papers, books, and scholarly works
- **Documents**: Archival materials and unpublished texts
- **Audiovisual**: Recordings and multimedia materials
- **References**: Bibliographic citations and author metadata

---

## Citation

If you use this dashboard in your research, please cite:

```
Madore, Frédérick. Islam West Africa Collection Dashboard.
https://fmadore.github.io/iwac-dashboard/
```

---

## For Developers

<details>
<summary>Technical details and contribution guide</summary>

### Technology Stack

- **Framework**: SvelteKit with Svelte 5, TypeScript
- **UI**: shadcn-svelte, Tailwind CSS v4
- **Visualizations**: LayerChart, D3.js, Leaflet, Sigma.js
- **Data**: Python scripts generating static JSON from Hugging Face

### Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Data Generation

```bash
cd scripts
pip install -r requirements.txt
python generate_overview_stats.py  # Run individual generators
```

### Project Structure

- `src/routes/` — Page components
- `src/lib/components/visualizations/` — Chart and map components
- `src/lib/stores/` — State management
- `scripts/` — Python data generation
- `static/data/` — Pre-computed JSON files

See [CLAUDE.md](./CLAUDE.md) for detailed development guidelines.

</details>

---

## License

This project is open source. The underlying dataset is available under its own license on Hugging Face.
