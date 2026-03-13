#!/usr/bin/env python3
"""generate_semantic_map.py
Generate 2D UMAP projection of article OCR embeddings for the Semantic Article Map.

INPUT:
    - HuggingFace dataset: fmadore/islam-west-africa-collection (articles subset)
      Uses embedding_OCR field (768-dim Gemini embeddings from full-text OCR)

OUTPUT:
    - static/data/semantic-map.json (all points)
    - static/data/semantic-map/<country-slug>.json (per-country files)
    - static/data/semantic-map/index.json (manifest with country list and counts)

The output includes:
    - points: array of {id, title, x, y, country, newspaper, date, topic, topicLabel, sentiment, polarity}
    - meta: generation metadata (total points, UMAP parameters, etc.)
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

import numpy as np

# Add scripts dir to path for iwac_utils
sys.path.insert(0, str(Path(__file__).parent))
from iwac_utils import (
    configure_logging,
    create_metadata_block,
    extract_year,
    load_dataset_safe,
    normalize_country,
    save_json,
)

# ------------------ Configuration ------------------
UMAP_N_NEIGHBORS = 15
UMAP_MIN_DIST = 0.1
UMAP_METRIC = "cosine"
UMAP_RANDOM_STATE = 42

# ------------------ Paths ------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "static" / "data"
OUT_FILE = DATA_DIR / "semantic-map.json"
PER_COUNTRY_DIR = DATA_DIR / "semantic-map"


def country_slug(name: str) -> str:
    """Convert country name to URL-friendly slug.

    Lowercase, replace spaces with hyphens, remove accents, strip non-alphanumeric.
    E.g. "Côte D'Ivoire" -> "cote-divoire"
    """
    # Decompose unicode and drop combining marks (accents)
    s = unicodedata.normalize("NFD", name)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    # Replace spaces with hyphens
    s = s.replace(" ", "-")
    # Remove anything that isn't alphanumeric or hyphen
    s = re.sub(r"[^a-z0-9-]", "", s)
    # Collapse multiple hyphens
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def main():
    log = configure_logging()

    # Load articles
    df = load_dataset_safe("articles")
    if df is None:
        log.error("Failed to load articles dataset")
        return

    log.info(f"Loaded {len(df)} articles")

    # Check for embedding_OCR column
    if "embedding_OCR" not in df.columns:
        log.error("embedding_OCR column not found in articles dataset")
        return

    # Filter to articles that have embeddings
    mask = df["embedding_OCR"].apply(lambda x: x is not None and len(x) > 0 if x is not None else False)
    df_with_emb = df[mask].copy()
    log.info(f"{len(df_with_emb)} articles have embedding_OCR ({len(df) - len(df_with_emb)} skipped)")

    if len(df_with_emb) < 10:
        log.error("Too few articles with embeddings to run UMAP")
        return

    # Extract embedding matrix
    log.info("Building embedding matrix...")
    embeddings = np.array(df_with_emb["embedding_OCR"].tolist(), dtype=np.float32)
    log.info(f"Embedding matrix shape: {embeddings.shape}")

    # Run UMAP
    log.info(f"Running UMAP (n_neighbors={UMAP_N_NEIGHBORS}, min_dist={UMAP_MIN_DIST})...")
    import umap

    reducer = umap.UMAP(
        n_neighbors=UMAP_N_NEIGHBORS,
        min_dist=UMAP_MIN_DIST,
        n_components=2,
        metric=UMAP_METRIC,
        random_state=UMAP_RANDOM_STATE,
    )
    coords = reducer.fit_transform(embeddings)
    log.info("UMAP complete")

    # Normalize coordinates to [0, 1] range for easier rendering
    x_min, x_max = coords[:, 0].min(), coords[:, 0].max()
    y_min, y_max = coords[:, 1].min(), coords[:, 1].max()
    coords[:, 0] = (coords[:, 0] - x_min) / (x_max - x_min)
    coords[:, 1] = (coords[:, 1] - y_min) / (y_max - y_min)

    # Build indexed lookup tables for compact output
    log.info("Building output points...")

    # Collect unique values first for index-based encoding
    all_countries = set()
    all_newspapers = set()
    topic_labels_map = {}  # topicId -> label

    for _, row in df_with_emb.iterrows():
        c = normalize_country(row.get("country"), return_list=False)
        if isinstance(c, str) and c and c != "Unknown":
            all_countries.add(c)
        np_val = row.get("newspaper")
        if np_val and str(np_val).strip():
            all_newspapers.add(str(np_val).strip())
        tid = row.get("lda_topic_id")
        if tid is not None and not (isinstance(tid, float) and np.isnan(tid)) and int(tid) >= 0:
            tlabel = row.get("lda_topic_label", "")
            if tlabel:
                parts = [p.strip().replace("_", " ") for p in str(tlabel).split(" - ")]
                topic_labels_map[int(tid)] = " - ".join(parts[:3])

    country_list = sorted(all_countries)
    newspaper_list = sorted(all_newspapers)
    country_idx = {c: i for i, c in enumerate(country_list)}
    newspaper_idx = {n: i for i, n in enumerate(newspaper_list)}

    # Sentiment/polarity use short codes to save space
    sentiment_codes = {"POSITIVE": "P", "NEGATIVE": "N", "NEUTRAL": "U"}
    polarity_codes = {
        "Très positif": "TP", "Positif": "P", "Neutre": "U",
        "Négatif": "N", "Très négatif": "TN", "Non applicable": "NA",
    }

    points = []
    for i, (_, row) in enumerate(df_with_emb.iterrows()):
        year = extract_year(row.get("pub_date"))
        country = normalize_country(row.get("country"), return_list=False)
        country = country if isinstance(country, str) else str(country)
        np_name = str(row.get("newspaper", "")).strip() if row.get("newspaper") else ""

        topic_id = row.get("lda_topic_id")
        topic_id = int(topic_id) if topic_id is not None and not (isinstance(topic_id, float) and np.isnan(topic_id)) else -1

        sentiment = str(row.get("sentiment_label", "")) if row.get("sentiment_label") else ""
        polarity = str(row.get("gemini_polarite", "")) if row.get("gemini_polarite") else ""

        # Compact point: use indices and short codes
        point = [
            int(row.get("o:id", i)),                          # 0: id
            str(row.get("title", ""))[:100],                   # 1: title
            round(float(coords[i, 0]), 4),                     # 2: x
            round(float(coords[i, 1]), 4),                     # 3: y
            country_idx.get(country, -1),                      # 4: country index
            newspaper_idx.get(np_name, -1),                    # 5: newspaper index
            year if year else 0,                               # 6: year
            topic_id,                                          # 7: topic id
            sentiment_codes.get(sentiment, ""),                # 8: sentiment code
            polarity_codes.get(polarity, ""),                  # 9: polarity code
        ]
        points.append(point)

    years = sorted(set(p[6] for p in points if p[6]))
    topics_sorted = sorted(topic_labels_map.items())

    output = {
        "p": points,  # compact: array of arrays
        "c": country_list,       # country lookup
        "n": newspaper_list,     # newspaper lookup
        "t": [{"id": tid, "label": tlabel} for tid, tlabel in topics_sorted],
        "sc": {v: k for k, v in sentiment_codes.items()},  # reverse lookup
        "pc": {v: k for k, v in polarity_codes.items()},   # reverse lookup
        "yr": [min(years), max(years)] if years else [0, 0],
        "meta": create_metadata_block(
            total_records=len(points),
            umapParams={
                "n_neighbors": UMAP_N_NEIGHBORS,
                "min_dist": UMAP_MIN_DIST,
                "metric": UMAP_METRIC,
            },
            embeddingDim=int(embeddings.shape[1]),
            skippedNoEmbedding=len(df) - len(df_with_emb),
        ),
    }

    save_json(output, OUT_FILE, minify=True)
    log.info(f"Done! {len(points)} points written to {OUT_FILE}")

    # ------------------------------------------------------------------
    # Per-country files
    # ------------------------------------------------------------------
    log.info("Generating per-country files...")

    # Group point indices by country index
    country_points: dict[int, list] = {}
    for pt in points:
        ci = pt[4]  # country index
        if ci < 0:
            continue
        country_points.setdefault(ci, []).append(pt)

    manifest_countries = []

    for ci, cname in enumerate(country_list):
        pts = country_points.get(ci, [])
        if not pts:
            continue

        slug = country_slug(cname)

        # Per-country years range
        c_years = sorted(set(p[6] for p in pts if p[6]))

        country_output = {
            "p": pts,
            "c": country_list,         # full lookup tables so types work unchanged
            "n": newspaper_list,
            "t": [{"id": tid, "label": tlabel} for tid, tlabel in topics_sorted],
            "sc": {v: k for k, v in sentiment_codes.items()},
            "pc": {v: k for k, v in polarity_codes.items()},
            "yr": [min(c_years), max(c_years)] if c_years else [0, 0],
            "meta": create_metadata_block(
                total_records=len(pts),
                country=cname,
                umapParams={
                    "n_neighbors": UMAP_N_NEIGHBORS,
                    "min_dist": UMAP_MIN_DIST,
                    "metric": UMAP_METRIC,
                },
                embeddingDim=int(embeddings.shape[1]),
            ),
        }

        save_json(country_output, PER_COUNTRY_DIR / f"{slug}.json", minify=True)
        manifest_countries.append({"slug": slug, "name": cname, "count": len(pts)})

    # Sort manifest by name
    manifest_countries.sort(key=lambda x: x["name"])

    manifest = {
        "countries": manifest_countries,
        "total": len(points),
    }
    save_json(manifest, PER_COUNTRY_DIR / "index.json", minify=True)
    log.info(f"Per-country files written for {len(manifest_countries)} countries to {PER_COUNTRY_DIR}")


if __name__ == "__main__":
    main()
