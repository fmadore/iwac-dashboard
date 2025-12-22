#!/usr/bin/env python3
"""build_networks.py
Generate co-occurrence network data for IWAC Spatial Overview (Sigma.js powered).

INPUT  (static JSON): omeka-map-explorer/static/data/entities/*.json
    Each file: [{ id, name, relatedArticleIds: string[], articleCount, ... }]

OUTPUT (JSON): omeka-map-explorer/static/data/networks/global.json
    nodes: [
        { id, type, label, count, degree, strength, labelPriority }
    ]
    edges: [
        { source, target, type, weight, weightNorm, articleIds }
    ]
    meta: {
        generatedAt, totalNodes, totalEdges, supportedTypes,
        weightMinConfigured, weightMinActual, weightMax,
        degree: { min, max, mean },
        strength: { min, max, mean },
        topLabelCount, typePairs
    }

WHY CHANGES (Sigma integration):
    * Pre-compute node "strength" (sum of incident edge weights) for advanced sizing/coloring.
    * Provide normalized edge weight (weightNorm) to avoid recomputing on client.
    * Provide labelPriority so the client can show top-N labels without scanning.
    * Include statistical metadata (degree/strength distributions) for UI scaling heuristics.

CLI OPTIONS (run `python build_networks.py -h`):
    --weight-min, --top-labels, --pairs, --no-cross-only
"""
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from statistics import fmean
import argparse

# ------------------ Configuration ------------------
DEFAULT_TYPE_PAIRS = [
    ("person", "organization"),
    ("event", "location"),
    ("person", "event"),
    ("organization", "event"),
    ("subject", "event"),
]

DEFAULT_WEIGHT_MIN = 2  # prune weak edges (configurable)
DEFAULT_TOP_LABELS = 60

# ------------------ Paths ------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'omeka-map-explorer' / 'static' / 'data'
ENT_DIR = DATA_DIR / 'entities'
OUT_DIR = DATA_DIR / 'networks'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------ Helpers ------------------
def load_entities(file: str):
    p = ENT_DIR / file
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding='utf-8'))

def build_article_index(entities: list[dict], type_key: str, 
                        article_to_entities: dict[str, dict[str, set[str]]],
                        node_info: dict[str, dict]):
    """
    Populate article_to_entities[articleId][type_key] with entity ids,
    and node_info with label/count for each node id.
    """
    for ent in entities:
        ent_id = str(ent.get('id'))
        node_id = f"{type_key}:{ent_id}"
        label = ent.get('name', '')
        count = int(ent.get('articleCount', len(ent.get('relatedArticleIds', []) or [])) or 0)
        node_info[node_id] = {
            'id': node_id,
            'type': type_key,
            'label': label,
            'count': count,
        }
        for aid in ent.get('relatedArticleIds', []) or []:
            aid = str(aid)
            bucket = article_to_entities.setdefault(aid, {})
            bucket.setdefault(type_key, set()).add(node_id)

# ------------------ Load ------------------
def parse_args():
    p = argparse.ArgumentParser(description="Build co-occurrence network JSON for IWAC")
    p.add_argument("--weight-min", type=int, default=DEFAULT_WEIGHT_MIN, help="Minimum edge weight to keep")
    p.add_argument("--top-labels", type=int, default=DEFAULT_TOP_LABELS, help="How many high-priority node labels to pre-compute")
    p.add_argument("--pairs", type=str, default="", help="Comma-separated type pairs 'a-b,c-d' (override defaults)")
    p.add_argument("--no-cross-only", action="store_true", help="If set, also build same-type co-occurrence edges")
    return p.parse_args()

ARGS = parse_args()

if ARGS.pairs:
    TYPE_PAIRS = [tuple(x.split("-", 1)) for x in ARGS.pairs.split(",") if "-" in x]
else:
    TYPE_PAIRS = DEFAULT_TYPE_PAIRS

WEIGHT_MIN = ARGS.weight_min
TOP_LABELS = ARGS.top_labels

print("Loading entity files...")
persons = load_entities('persons.json')
organizations = load_entities('organizations.json')
events = load_entities('events.json')
subjects = load_entities('subjects.json')
locations = load_entities('locations.json')

print(
    f"Loaded persons={len(persons)}, orgs={len(organizations)}, events={len(events)}, subjects={len(subjects)}, locations={len(locations)}"
)

# ------------------ Index ------------------
article_to_entities: dict[str, dict[str, set[str]]] = {}
node_info: dict[str, dict] = {}

build_article_index(persons, 'person', article_to_entities, node_info)
build_article_index(organizations, 'organization', article_to_entities, node_info)
build_article_index(events, 'event', article_to_entities, node_info)
build_article_index(subjects, 'subject', article_to_entities, node_info)
build_article_index(locations, 'location', article_to_entities, node_info)

print(f"Indexed {len(article_to_entities)} articles with at least one entity.")

def accumulate_edge(aid: str, t1: str, t2: str, a_nodes: set[str], b_nodes: set[str], acc: dict):
    for n1 in a_nodes:
        for n2 in b_nodes:
            s, t = (n1, n2) if n1 < n2 else (n2, n1)
            key = (s, t)
            rec = acc.get(key)
            if not rec:
                acc[key] = {
                    'source': s,
                    'target': t,
                    'type': f"{t1}-{t2}",
                    'weight': 1,
                    'articleIds': [aid],
                }
            else:
                rec['weight'] += 1
                if not rec['articleIds'] or rec['articleIds'][-1] != aid:
                    rec['articleIds'].append(aid)

edge_acc: dict[tuple[str, str], dict] = {}

for aid, by_type in article_to_entities.items():
    # cross-type pairs
    for t1, t2 in TYPE_PAIRS:
        a = by_type.get(t1)
        b = by_type.get(t2)
        if a and b:
            accumulate_edge(aid, t1, t2, a, b, edge_acc)
    # optional same-type pairs if requested
    if ARGS.no_cross_only:
        for t, nodeset in by_type.items():
            if len(nodeset) < 2:
                continue
            # all unordered pairs inside nodeset
            lst = sorted(nodeset)
            for i in range(len(lst)):
                for j in range(i + 1, len(lst)):
                    s, t2 = lst[i], lst[j]
                    key = (s, t2)
                    rec = edge_acc.get(key)
                    if not rec:
                        edge_acc[key] = {
                            'source': s,
                            'target': t2,
                            'type': f"{t}-{t}",
                            'weight': 1,
                            'articleIds': [aid],
                        }
                    else:
                        rec['weight'] += 1
                        if rec['articleIds'][-1] != aid:
                            rec['articleIds'].append(aid)

# Prune weak edges
edges = [e for e in edge_acc.values() if e['weight'] >= WEIGHT_MIN]
edges.sort(key=lambda r: r['weight'], reverse=True)

# ------------------ Build nodes subset ------------------
used_ids: set[str] = set()
for e in edges:
    used_ids.add(e['source'])
    used_ids.add(e['target'])

nodes = [node_info[nid] for nid in used_ids]

# Degree & strength (sum of incident edge weights)
degree = {nid: 0 for nid in used_ids}
strength = {nid: 0 for nid in used_ids}
for e in edges:
    degree[e['source']] += 1
    degree[e['target']] += 1
    strength[e['source']] += e['weight']
    strength[e['target']] += e['weight']
for n in nodes:
    nid = n['id']
    n['degree'] = degree.get(nid, 0)
    n['strength'] = strength.get(nid, 0)

# Edge weight normalization
if edges:
    max_w = max(e['weight'] for e in edges)
    min_w = min(e['weight'] for e in edges)
else:
    max_w = min_w = 1
for e in edges:
    e['weightNorm'] = round(e['weight'] / max_w, 6) if max_w else 0

# Label priority (higher = more important) used by client for top labels
nodes.sort(key=lambda x: (x['degree'] * 3 + x['count']), reverse=True)
for idx, n in enumerate(nodes):
    n['labelPriority'] = idx + 1

# Truncate top labels list length (still store priority for all)
top_label_slice = nodes[:TOP_LABELS]

deg_vals = [n['degree'] for n in nodes] or [0]
str_vals = [n['strength'] for n in nodes] or [0]

output = {
    'nodes': nodes,  # already sorted by label priority importance
    'edges': edges,
    'meta': {
        'generatedAt': datetime.utcnow().isoformat() + 'Z',
        'totalNodes': len(nodes),
        'totalEdges': len(edges),
        'supportedTypes': ['person', 'organization', 'event', 'subject', 'location'],
        'weightMinConfigured': WEIGHT_MIN,
        'weightMinActual': min_w,
        'weightMax': max_w,
        'degree': {
            'min': min(deg_vals),
            'max': max(deg_vals),
            'mean': round(fmean(deg_vals), 3),
        },
        'strength': {
            'min': min(str_vals),
            'max': max(str_vals),
            'mean': round(fmean(str_vals), 3),
        },
        'topLabelCount': TOP_LABELS,
        'typePairs': TYPE_PAIRS,
        'labelPriorityTop': [n['id'] for n in top_label_slice],
    },
}

(OUT_DIR / 'global.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
print(
    f"Wrote {OUT_DIR / 'global.json'} (nodes={len(nodes)}, edges={len(edges)}, maxW={max_w}, topLabels={TOP_LABELS})"
)
