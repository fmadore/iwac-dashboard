#!/usr/bin/env python3
"""
Generate Knowledge Graph from IWAC Dataset

INPUT:
  - HuggingFace: fmadore/islam-west-africa-collection (index, articles, references)
  - Existing: static/data/entities/locations.json (for coordinates)

OUTPUT:
  - static/data/knowledge-graph/graph.json       (core KG: entities + typed edges)
  - static/data/knowledge-graph/ontology.json     (schema definition)
  - static/data/knowledge-graph/stats.json        (extraction statistics)

EDGE TYPES:
  Explicit (from index relational fields):
    - part_of        : "Partie de" field
    - has_part        : "A une partie" field
    - related_to      : "Relation" field
    - succeeded_by    : "Remplacé par" field
    - located_in      : "spatial" field on index entities

  Inferred (from article/reference metadata):
    - mentioned_in    : entity name in article.subject
    - co_occurs_with  : two entities in same article.subject (weighted)
    - co_authored_with: two authors on same reference
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import unicodedata
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from iwac_utils import (
    configure_logging,
    find_column,
    generate_timestamp,
    load_dataset_safe,
    normalize_location_name,
    parse_coordinates,
    parse_pipe_separated,
    save_json,
)

logger = logging.getLogger(__name__)

# Paths
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "static" / "data"
OUT_DIR = DATA_DIR / "knowledge-graph"

# Entity type mapping (French → English)
TYPE_MAP = {
    "Personnes": "Person",
    "Organisations": "Organization",
    "Lieux": "Place",
    "Événements": "Event",
    "Sujets": "Subject",
    "Notices d'autorité": "Authority",
}

# Reverse map for lookups
TYPE_MAP_REV = {v: k for k, v in TYPE_MAP.items()}


def normalize_name(name: str) -> str:
    """Normalize entity name for matching: NFC + lowercase + collapse whitespace."""
    if not name:
        return ""
    name = unicodedata.normalize("NFC", str(name).strip().lower())
    name = " ".join(name.split())
    return name


def make_node_id(entity_type: str, omeka_id: Any) -> str:
    """Create a prefixed node ID."""
    prefix_map = {
        "Person": "per",
        "Organization": "org",
        "Place": "plc",
        "Event": "evt",
        "Subject": "sub",
        "Authority": "aut",
        "Article": "art",
        "Reference": "ref",
        "Topic": "top",
    }
    prefix = prefix_map.get(entity_type, "unk")
    return f"{prefix}:{omeka_id}"


class KnowledgeGraphBuilder:
    """Builds a knowledge graph from IWAC dataset subsets."""

    def __init__(
        self,
        min_cooccurrence: int = 3,
        max_article_nodes: int = 0,
        include_articles: bool = False,
    ):
        self.min_cooccurrence = min_cooccurrence
        self.max_article_nodes = max_article_nodes
        self.include_articles = include_articles

        # Data
        self.index_df = None
        self.articles_df = None
        self.references_df = None

        # Graph structures
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[Dict] = []
        self.edge_set: Set[Tuple[str, str, str]] = set()  # (source, target, type) dedup

        # Lookup tables
        self.name_to_id: Dict[str, str] = {}  # normalized name → node ID
        self.alt_name_to_id: Dict[str, str] = {}  # alt names → node ID
        self.id_to_name: Dict[str, str] = {}  # node ID → display name

        # Statistics
        self.stats = {
            "explicit_edges": Counter(),
            "inferred_edges": Counter(),
            "match_success": 0,
            "match_failure": 0,
            "unmatched_names": Counter(),
        }

    def load_data(self) -> None:
        """Load required HuggingFace subsets."""
        self.index_df = load_dataset_safe("index")
        self.articles_df = load_dataset_safe("articles")
        self.references_df = load_dataset_safe("references")

        if self.index_df is None:
            raise RuntimeError("Failed to load index subset")
        if self.articles_df is None:
            raise RuntimeError("Failed to load articles subset")

    def build_entity_lookup(self) -> None:
        """Build name → ID lookup tables from the index subset."""
        df = self.index_df

        title_col = find_column(df, ["Titre", "dcterms:title", "title"])
        alt_col = find_column(df, ["Titre alternatif", "dcterms:alternative"])
        type_col = find_column(df, ["Type", "type"])
        id_col = find_column(df, ["o:id", "id"])

        for _, row in df.iterrows():
            raw_type = str(row.get(type_col, "")).strip() if type_col else ""
            entity_type = TYPE_MAP.get(raw_type, "Authority")
            omeka_id = row.get(id_col, "")
            node_id = make_node_id(entity_type, omeka_id)
            title = str(row.get(title_col, "")).strip() if title_col else ""

            if not title:
                continue

            # Primary name
            norm = normalize_name(title)
            if norm:
                self.name_to_id[norm] = node_id
                self.id_to_name[node_id] = title

            # Alternative names
            if alt_col:
                for alt in parse_pipe_separated(row.get(alt_col)):
                    norm_alt = normalize_name(alt)
                    if norm_alt and norm_alt not in self.name_to_id:
                        self.alt_name_to_id[norm_alt] = node_id

        logger.info(
            f"Entity lookup: {len(self.name_to_id)} primary names, "
            f"{len(self.alt_name_to_id)} alternative names"
        )

    def resolve_name(self, name: str) -> Optional[str]:
        """Resolve an entity name to a node ID. Returns None if not found."""
        norm = normalize_name(name)
        if not norm:
            return None

        # Try primary names first
        node_id = self.name_to_id.get(norm)
        if node_id:
            self.stats["match_success"] += 1
            return node_id

        # Try alternative names
        node_id = self.alt_name_to_id.get(norm)
        if node_id:
            self.stats["match_success"] += 1
            return node_id

        self.stats["match_failure"] += 1
        self.stats["unmatched_names"][name] += 1
        return None

    def build_entity_nodes(self) -> None:
        """Create nodes from the index subset."""
        df = self.index_df

        title_col = find_column(df, ["Titre", "dcterms:title", "title"])
        type_col = find_column(df, ["Type", "type"])
        id_col = find_column(df, ["o:id", "id"])
        freq_col = find_column(df, ["frequency"])
        first_col = find_column(df, ["first_occurrence"])
        last_col = find_column(df, ["last_occurrence"])
        countries_col = find_column(df, ["countries"])
        coords_col = find_column(df, ["Coordonnées", "coordinates"])
        desc_col = find_column(df, ["Description", "description"])
        spatial_col = find_column(df, ["spatial"])
        gender_col = find_column(df, ["Genre", "gender"])
        birth_col = find_column(df, ["Naissance", "birth"])
        url_col = find_column(df, ["url"])

        node_count = Counter()

        for _, row in df.iterrows():
            raw_type = str(row.get(type_col, "")).strip() if type_col else ""
            entity_type = TYPE_MAP.get(raw_type, "Authority")
            omeka_id = row.get(id_col, "")
            node_id = make_node_id(entity_type, omeka_id)
            title = str(row.get(title_col, "")).strip() if title_col else ""

            if not title:
                continue

            node = {
                "id": node_id,
                "type": entity_type,
                "label": title,
            }

            # Optional properties
            props = {}

            if freq_col and not _is_empty(row.get(freq_col)):
                props["frequency"] = int(row[freq_col])

            if first_col and not _is_empty(row.get(first_col)):
                props["firstOccurrence"] = str(row[first_col]).strip()

            if last_col and not _is_empty(row.get(last_col)):
                props["lastOccurrence"] = str(row[last_col]).strip()

            if countries_col and not _is_empty(row.get(countries_col)):
                props["countries"] = parse_pipe_separated(row[countries_col])

            if coords_col and not _is_empty(row.get(coords_col)):
                coords = parse_coordinates(row[coords_col])
                if coords:
                    props["coordinates"] = list(coords)

            if spatial_col and not _is_empty(row.get(spatial_col)):
                props["spatial"] = parse_pipe_separated(row[spatial_col])

            if gender_col and not _is_empty(row.get(gender_col)):
                props["gender"] = str(row[gender_col]).strip()

            if birth_col and not _is_empty(row.get(birth_col)):
                props["birthDate"] = str(row[birth_col]).strip()

            if desc_col and not _is_empty(row.get(desc_col)):
                desc = str(row[desc_col]).strip()
                if len(desc) > 300:
                    desc = desc[:297] + "..."
                props["description"] = desc

            if url_col and not _is_empty(row.get(url_col)):
                props["url"] = str(row[url_col]).strip()

            if props:
                node["properties"] = props

            self.nodes[node_id] = node
            node_count[entity_type] += 1

        for t, c in node_count.most_common():
            logger.info(f"  {t}: {c} nodes")
        logger.info(f"Total entity nodes: {len(self.nodes)}")

    def add_edge(
        self,
        source: str,
        target: str,
        edge_type: str,
        weight: float = 1.0,
        properties: Optional[Dict] = None,
    ) -> bool:
        """Add an edge, deduplicating by (source, target, type)."""
        if source == target:
            return False

        # Normalize direction for undirected edge types
        undirected = {"co_occurs_with", "co_authored_with", "related_to"}
        if edge_type in undirected:
            key = (min(source, target), max(source, target), edge_type)
        else:
            key = (source, target, edge_type)

        if key in self.edge_set:
            # Update weight if co-occurrence
            if edge_type in {"co_occurs_with", "co_authored_with"}:
                for e in self.edges:
                    s, t = (min(source, target), max(source, target))
                    if (
                        edge_type in undirected
                        and min(e["source"], e["target"]) == s
                        and max(e["source"], e["target"]) == t
                        and e["type"] == edge_type
                    ):
                        e["weight"] += weight
                        break
            return False

        self.edge_set.add(key)
        edge = {
            "source": key[0] if edge_type in undirected else source,
            "target": key[1] if edge_type in undirected else target,
            "type": edge_type,
            "weight": weight,
        }
        if properties:
            edge["properties"] = properties
        self.edges.append(edge)
        return True

    def extract_explicit_edges(self) -> None:
        """Extract typed edges from index relational fields."""
        df = self.index_df

        id_col = find_column(df, ["o:id", "id"])
        type_col = find_column(df, ["Type", "type"])
        title_col = find_column(df, ["Titre", "dcterms:title", "title"])

        # Field → edge type mapping
        rel_fields = {
            "Relation": "related_to",
            "Partie de": "part_of",
            "A une partie": "has_part",
            "Remplacé par": "succeeded_by",
        }

        for field_name, edge_type in rel_fields.items():
            col = find_column(df, [field_name])
            if not col:
                logger.warning(f"Column '{field_name}' not found, skipping")
                continue

            count = 0
            for _, row in df.iterrows():
                raw_type = str(row.get(type_col, "")).strip() if type_col else ""
                entity_type = TYPE_MAP.get(raw_type, "Authority")
                omeka_id = row.get(id_col, "")
                source_id = make_node_id(entity_type, omeka_id)

                if source_id not in self.nodes:
                    continue

                targets = parse_pipe_separated(row.get(col))
                for target_name in targets:
                    target_id = self.resolve_name(target_name)
                    if target_id and target_id in self.nodes:
                        added = self.add_edge(
                            source_id,
                            target_id,
                            edge_type,
                            properties={"source": "index"},
                        )
                        if added:
                            count += 1

            self.stats["explicit_edges"][edge_type] = count
            logger.info(f"  {edge_type}: {count} edges")

        # Spatial edges: entity → place (from index spatial field)
        spatial_col = find_column(df, ["spatial"])
        if spatial_col:
            count = 0
            for _, row in df.iterrows():
                raw_type = str(row.get(type_col, "")).strip() if type_col else ""
                entity_type = TYPE_MAP.get(raw_type, "Authority")

                # Skip places linking to places (avoid trivial self-location)
                if entity_type == "Place":
                    continue

                omeka_id = row.get(id_col, "")
                source_id = make_node_id(entity_type, omeka_id)

                if source_id not in self.nodes:
                    continue

                locations = parse_pipe_separated(row.get(spatial_col))
                for loc_name in locations:
                    loc_id = self.resolve_name(loc_name)
                    if loc_id and loc_id in self.nodes:
                        added = self.add_edge(
                            source_id,
                            loc_id,
                            "located_in",
                            properties={"source": "index"},
                        )
                        if added:
                            count += 1

            self.stats["explicit_edges"]["located_in"] = count
            logger.info(f"  located_in: {count} edges")

    def extract_article_edges(self) -> None:
        """Extract entity co-occurrence from article subject fields."""
        df = self.articles_df
        if df is None:
            return

        subject_col = find_column(df, ["subject", "dcterms:subject"])
        id_col = find_column(df, ["o:id", "id"])

        if not subject_col:
            logger.warning("No subject column in articles, skipping co-occurrence")
            return

        # Accumulate co-occurrence weights
        cooccurrence: Dict[Tuple[str, str], int] = defaultdict(int)
        mention_count = 0

        for _, row in df.iterrows():
            subjects = parse_pipe_separated(row.get(subject_col))
            article_id = str(row.get(id_col, ""))

            # Resolve each subject to an entity node
            resolved = []
            for subj in subjects:
                node_id = self.resolve_name(subj)
                if node_id and node_id in self.nodes:
                    resolved.append(node_id)

            # Co-occurrence: all pairs of resolved entities
            for a, b in combinations(set(resolved), 2):
                key = (min(a, b), max(a, b))
                cooccurrence[key] += 1

        # Add co-occurrence edges above threshold
        cooc_count = 0
        for (a, b), weight in cooccurrence.items():
            if weight >= self.min_cooccurrence:
                edge = {
                    "source": a,
                    "target": b,
                    "type": "co_occurs_with",
                    "weight": weight,
                }
                key = (a, b, "co_occurs_with")
                if key not in self.edge_set:
                    self.edge_set.add(key)
                    self.edges.append(edge)
                    cooc_count += 1

        self.stats["inferred_edges"]["co_occurs_with"] = cooc_count
        logger.info(f"  co_occurs_with: {cooc_count} edges (min weight: {self.min_cooccurrence})")

    def extract_reference_edges(self) -> None:
        """Extract co-authorship edges from references."""
        df = self.references_df
        if df is None:
            logger.warning("No references data, skipping co-authorship")
            return

        author_col = find_column(df, ["author", "dcterms:creator"])
        if not author_col:
            logger.warning("No author column in references, skipping")
            return

        coauthor: Dict[Tuple[str, str], int] = defaultdict(int)

        for _, row in df.iterrows():
            authors = parse_pipe_separated(row.get(author_col))
            if len(authors) < 2:
                continue

            # Resolve authors to entity nodes
            resolved = []
            for author in authors:
                node_id = self.resolve_name(author)
                if node_id and node_id in self.nodes:
                    resolved.append(node_id)

            for a, b in combinations(set(resolved), 2):
                key = (min(a, b), max(a, b))
                coauthor[key] += 1

        count = 0
        for (a, b), weight in coauthor.items():
            edge = {
                "source": a,
                "target": b,
                "type": "co_authored_with",
                "weight": weight,
            }
            key = (a, b, "co_authored_with")
            if key not in self.edge_set:
                self.edge_set.add(key)
                self.edges.append(edge)
                count += 1

        self.stats["inferred_edges"]["co_authored_with"] = count
        logger.info(f"  co_authored_with: {count} edges")

    def compute_graph_metrics(self) -> None:
        """Compute degree, strength, and normalize edge weights."""
        # Compute degree and strength per node
        degree: Counter = Counter()
        strength: Dict[str, float] = defaultdict(float)

        for edge in self.edges:
            s, t = edge["source"], edge["target"]
            degree[s] += 1
            degree[t] += 1
            strength[s] += edge.get("weight", 1.0)
            strength[t] += edge.get("weight", 1.0)

        # Attach to nodes
        for node_id, node in self.nodes.items():
            node["degree"] = degree.get(node_id, 0)
            node["strength"] = round(strength.get(node_id, 0.0), 2)

        # Normalize edge weights per type
        edges_by_type: Dict[str, List[Dict]] = defaultdict(list)
        for edge in self.edges:
            edges_by_type[edge["type"]].append(edge)

        for edge_type, type_edges in edges_by_type.items():
            weights = [e["weight"] for e in type_edges]
            if not weights:
                continue
            min_w = min(weights)
            max_w = max(weights)
            w_range = max_w - min_w
            for edge in type_edges:
                if w_range > 0:
                    edge["weightNorm"] = round(
                        (edge["weight"] - min_w) / w_range, 4
                    )
                else:
                    edge["weightNorm"] = 1.0

        # Label priority (by strength, for rendering)
        sorted_nodes = sorted(
            self.nodes.values(),
            key=lambda n: n.get("strength", 0),
            reverse=True,
        )
        for rank, node in enumerate(sorted_nodes):
            node["labelPriority"] = rank

    def remove_isolated_nodes(self) -> int:
        """Remove nodes with no edges. Returns count removed."""
        connected = set()
        for edge in self.edges:
            connected.add(edge["source"])
            connected.add(edge["target"])

        isolated = [nid for nid in self.nodes if nid not in connected]
        for nid in isolated:
            del self.nodes[nid]

        if isolated:
            logger.info(f"Removed {len(isolated)} isolated nodes")
        return len(isolated)

    def build_ontology(self) -> Dict:
        """Generate ontology/schema definition."""
        return {
            "nodeTypes": {
                "Person": {
                    "label": {"en": "Person", "fr": "Personne"},
                    "color": "var(--chart-1)",
                    "description": {
                        "en": "Individual people (religious figures, politicians, intellectuals)",
                        "fr": "Individus (figures religieuses, politiciens, intellectuels)",
                    },
                },
                "Organization": {
                    "label": {"en": "Organization", "fr": "Organisation"},
                    "color": "var(--chart-2)",
                    "description": {
                        "en": "Islamic associations, NGOs, movements, institutions",
                        "fr": "Associations islamiques, ONG, mouvements, institutions",
                    },
                },
                "Place": {
                    "label": {"en": "Place", "fr": "Lieu"},
                    "color": "var(--chart-3)",
                    "description": {
                        "en": "Cities, regions, countries, mosques",
                        "fr": "Villes, régions, pays, mosquées",
                    },
                },
                "Event": {
                    "label": {"en": "Event", "fr": "Événement"},
                    "color": "var(--chart-4)",
                    "description": {
                        "en": "Conferences, congresses, elections, festivals",
                        "fr": "Conférences, congrès, élections, festivals",
                    },
                },
                "Subject": {
                    "label": {"en": "Subject", "fr": "Sujet"},
                    "color": "var(--chart-5)",
                    "description": {
                        "en": "Thematic topics and keywords",
                        "fr": "Sujets thématiques et mots-clés",
                    },
                },
                "Authority": {
                    "label": {"en": "Authority Record", "fr": "Notice d'autorité"},
                    "color": "var(--muted)",
                    "description": {
                        "en": "Authority records and cross-references",
                        "fr": "Notices d'autorité et renvois",
                    },
                },
            },
            "edgeTypes": {
                "part_of": {
                    "label": {"en": "Part of", "fr": "Partie de"},
                    "directed": True,
                    "layer": "explicit",
                    "description": {
                        "en": "Hierarchical membership or containment",
                        "fr": "Appartenance hiérarchique",
                    },
                },
                "has_part": {
                    "label": {"en": "Has part", "fr": "A une partie"},
                    "directed": True,
                    "layer": "explicit",
                    "description": {
                        "en": "Inverse of part_of",
                        "fr": "Inverse de partie de",
                    },
                },
                "related_to": {
                    "label": {"en": "Related to", "fr": "Lié à"},
                    "directed": False,
                    "layer": "explicit",
                    "description": {
                        "en": "General relationship between entities",
                        "fr": "Relation générale entre entités",
                    },
                },
                "succeeded_by": {
                    "label": {"en": "Succeeded by", "fr": "Remplacé par"},
                    "directed": True,
                    "layer": "explicit",
                    "description": {
                        "en": "Temporal succession",
                        "fr": "Succession temporelle",
                    },
                },
                "located_in": {
                    "label": {"en": "Located in", "fr": "Situé à"},
                    "directed": True,
                    "layer": "explicit",
                    "description": {
                        "en": "Entity is located in or associated with a place",
                        "fr": "Entité située ou associée à un lieu",
                    },
                },
                "co_occurs_with": {
                    "label": {"en": "Co-occurs with", "fr": "Co-occurrence avec"},
                    "directed": False,
                    "layer": "inferred",
                    "description": {
                        "en": "Entities frequently mentioned together in articles",
                        "fr": "Entités fréquemment mentionnées ensemble dans les articles",
                    },
                },
                "co_authored_with": {
                    "label": {"en": "Co-authored with", "fr": "Co-auteur avec"},
                    "directed": False,
                    "layer": "inferred",
                    "description": {
                        "en": "Authors who co-wrote academic references",
                        "fr": "Auteurs ayant co-écrit des références académiques",
                    },
                },
            },
        }

    def build_stats(self) -> Dict:
        """Generate extraction statistics."""
        # Node type distribution
        type_counts = Counter()
        for node in self.nodes.values():
            type_counts[node["type"]] += 1

        # Edge type distribution
        edge_type_counts = Counter()
        edge_type_weights = defaultdict(list)
        for edge in self.edges:
            edge_type_counts[edge["type"]] += 1
            edge_type_weights[edge["type"]].append(edge.get("weight", 1.0))

        # Edge weight stats per type
        edge_weight_stats = {}
        for etype, weights in edge_type_weights.items():
            edge_weight_stats[etype] = {
                "count": len(weights),
                "minWeight": round(min(weights), 2),
                "maxWeight": round(max(weights), 2),
                "avgWeight": round(sum(weights) / len(weights), 2),
            }

        # Degree distribution
        degrees = [n.get("degree", 0) for n in self.nodes.values()]
        connected_degrees = [d for d in degrees if d > 0]

        # Name matching stats
        total_matches = self.stats["match_success"] + self.stats["match_failure"]
        match_rate = (
            self.stats["match_success"] / total_matches * 100
            if total_matches > 0
            else 0
        )

        # Top unmatched names
        top_unmatched = [
            {"name": name, "count": count}
            for name, count in self.stats["unmatched_names"].most_common(50)
        ]

        return {
            "generatedAt": generate_timestamp(),
            "summary": {
                "totalNodes": len(self.nodes),
                "totalEdges": len(self.edges),
                "explicitEdges": sum(self.stats["explicit_edges"].values()),
                "inferredEdges": sum(self.stats["inferred_edges"].values()),
            },
            "nodesByType": dict(type_counts.most_common()),
            "edgesByType": dict(edge_type_counts.most_common()),
            "edgeWeightStats": edge_weight_stats,
            "degreeDistribution": {
                "min": min(degrees) if degrees else 0,
                "max": max(degrees) if degrees else 0,
                "mean": round(sum(degrees) / len(degrees), 2) if degrees else 0,
                "connectedNodes": len(connected_degrees),
                "isolatedNodes": len(degrees) - len(connected_degrees),
            },
            "nameMatching": {
                "totalAttempts": total_matches,
                "successes": self.stats["match_success"],
                "failures": self.stats["match_failure"],
                "matchRate": round(match_rate, 1),
                "topUnmatched": top_unmatched,
            },
            "explicitEdgeBreakdown": dict(self.stats["explicit_edges"]),
            "inferredEdgeBreakdown": dict(self.stats["inferred_edges"]),
        }

    def build(self) -> Dict:
        """Run the full knowledge graph pipeline."""
        logger.info("=" * 60)
        logger.info("IWAC Knowledge Graph Generation")
        logger.info("=" * 60)

        # Load data
        self.load_data()

        # Build lookup tables
        logger.info("\n--- Building entity lookup ---")
        self.build_entity_lookup()

        # Build nodes
        logger.info("\n--- Building entity nodes ---")
        self.build_entity_nodes()

        # Extract explicit edges
        logger.info("\n--- Extracting explicit edges (index fields) ---")
        self.extract_explicit_edges()

        # Extract co-occurrence from articles
        logger.info("\n--- Extracting article co-occurrence ---")
        self.extract_article_edges()

        # Extract co-authorship from references
        logger.info("\n--- Extracting reference co-authorship ---")
        self.extract_reference_edges()

        # Remove isolated nodes
        logger.info("\n--- Cleaning graph ---")
        self.remove_isolated_nodes()

        # Compute metrics
        logger.info("\n--- Computing graph metrics ---")
        self.compute_graph_metrics()

        # Build outputs
        graph = {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "meta": {
                "generatedAt": generate_timestamp(),
                "totalNodes": len(self.nodes),
                "totalEdges": len(self.edges),
                "dataSource": "fmadore/islam-west-africa-collection",
                "minCooccurrence": self.min_cooccurrence,
            },
        }

        return graph


def _is_empty(val: Any) -> bool:
    """Check if a value is empty/missing."""
    if val is None:
        return True
    try:
        import pandas as pd
        if pd.isna(val):
            return True
    except (TypeError, ValueError):
        pass
    if isinstance(val, str) and not val.strip():
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Generate IWAC Knowledge Graph")
    parser.add_argument(
        "--min-cooccurrence",
        type=int,
        default=3,
        help="Minimum article co-occurrence count for inferred edges (default: 3)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(OUT_DIR),
        help="Output directory for JSON files",
    )
    args = parser.parse_args()

    configure_logging()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    builder = KnowledgeGraphBuilder(
        min_cooccurrence=args.min_cooccurrence,
    )

    # Build graph
    graph = builder.build()

    # Build ontology and stats
    ontology = builder.build_ontology()
    stats = builder.build_stats()

    # Save outputs
    logger.info("\n--- Saving outputs ---")
    save_json(graph, out_dir / "graph.json", minify=True)
    save_json(ontology, out_dir / "ontology.json", minify=False)
    save_json(stats, out_dir / "stats.json", minify=False)

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("KNOWLEDGE GRAPH SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Nodes: {stats['summary']['totalNodes']}")
    logger.info(f"Edges: {stats['summary']['totalEdges']}")
    logger.info(f"  Explicit: {stats['summary']['explicitEdges']}")
    logger.info(f"  Inferred: {stats['summary']['inferredEdges']}")
    logger.info(f"Name match rate: {stats['nameMatching']['matchRate']}%")
    logger.info(f"\nNode types: {stats['nodesByType']}")
    logger.info(f"Edge types: {stats['edgesByType']}")
    logger.info(f"\nOutputs written to: {out_dir}")


if __name__ == "__main__":
    main()
