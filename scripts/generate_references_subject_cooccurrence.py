#!/usr/bin/env python3
"""
Generate subject co-occurrence network data for IWAC references.

Creates a network where:
- Nodes are unique subject keywords from references
- Edges connect subjects that appear together on the same reference
- Edge weight is the number of references sharing both subjects

Output: static/data/references/subject-cooccurrence.json
"""

import hashlib
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

# Add scripts directory to path for iwac_utils
sys.path.insert(0, str(Path(__file__).parent))

from iwac_utils import (
    configure_logging,
    load_dataset_safe,
    parse_pipe_separated,
    save_json,
)

logger = configure_logging()

OUTPUT_DIR = Path(__file__).parent.parent / "static" / "data" / "references"


def make_subject_id(label: str) -> str:
    """Create a stable ID for a subject."""
    hash_val = hashlib.md5(label.encode("utf-8")).hexdigest()[:8]
    return f"subject:{hash_val}"


def generate_subject_cooccurrence(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate subject co-occurrence network data.

    Creates a network where:
    - Nodes are unique subject keywords
    - Edges connect subjects that co-occur on the same reference
    - Edge weight is the number of references with both subjects
    """
    logger.info("Generating subject co-occurrence network...")

    # Build reference -> subjects mapping
    ref_subjects: Dict[str, set] = defaultdict(set)
    subject_refs: Dict[str, set] = defaultdict(set)

    for record in records:
        subjects = parse_pipe_separated(record.get("subject"))
        if len(subjects) < 2:
            continue

        pub_id = record.get("pub_id", record.get("o:id", ""))
        if not pub_id:
            continue

        pub_id = str(pub_id)
        for subj in subjects:
            ref_subjects[pub_id].add(subj)
            subject_refs[subj].add(pub_id)

    logger.info(f"Found {len(ref_subjects)} references with 2+ subjects")
    logger.info(f"Found {len(subject_refs)} unique subjects")

    # Build co-occurrence edges
    edge_weights: Dict[tuple, Dict] = {}

    for pub_id, subjects in ref_subjects.items():
        subjects_list = sorted(subjects)

        for i, subj1 in enumerate(subjects_list):
            for subj2 in subjects_list[i + 1 :]:
                edge_key = (subj1, subj2)

                if edge_key not in edge_weights:
                    edge_weights[edge_key] = {"weight": 0, "pub_ids": set()}

                edge_weights[edge_key]["weight"] += 1
                edge_weights[edge_key]["pub_ids"].add(pub_id)

    logger.info(f"Found {len(edge_weights)} unique subject co-occurrence pairs")

    if not edge_weights:
        return {
            "nodes": [],
            "edges": [],
            "meta": {
                "generatedAt": "",
                "totalNodes": 0,
                "totalEdges": 0,
                "supportedTypes": ["subject"],
                "weightMinConfigured": 1,
                "weightMinActual": 0,
                "weightMax": 0,
                "degree": {"min": 0, "max": 0, "mean": 0},
                "strength": {"min": 0, "max": 0, "mean": 0},
                "topLabelCount": 50,
                "typePairs": [["subject", "subject"]],
                "labelPriorityTop": [],
            },
        }

    # Compute node metrics
    subject_degree: Dict[str, int] = defaultdict(int)
    subject_strength: Dict[str, int] = defaultdict(int)

    for (subj1, subj2), data in edge_weights.items():
        weight = data["weight"]
        subject_degree[subj1] += 1
        subject_degree[subj2] += 1
        subject_strength[subj1] += weight
        subject_strength[subj2] += weight

    all_subjects = set(subject_degree.keys())

    # Sort subjects by strength for label priority
    sorted_subjects = sorted(all_subjects, key=lambda s: subject_strength[s], reverse=True)
    subject_priority = {subj: idx for idx, subj in enumerate(sorted_subjects)}

    # Build nodes
    subject_id_map = {}
    nodes = []

    for subj in all_subjects:
        subj_id = make_subject_id(subj)
        subject_id_map[subj] = subj_id

        nodes.append(
            {
                "id": subj_id,
                "type": "subject",
                "label": subj,
                "count": len(subject_refs.get(subj, set())),
                "degree": subject_degree[subj],
                "strength": subject_strength[subj],
                "labelPriority": subject_priority[subj],
            }
        )

    # Build edges
    max_weight = max(data["weight"] for data in edge_weights.values())

    edges = []
    for (subj1, subj2), data in edge_weights.items():
        weight = data["weight"]
        edges.append(
            {
                "source": subject_id_map[subj1],
                "target": subject_id_map[subj2],
                "type": "subject-subject",
                "weight": weight,
                "weightNorm": weight / max_weight if max_weight > 0 else 0,
                "articleIds": list(data["pub_ids"])[:100],
            }
        )

    # Sort edges by weight descending
    edges.sort(key=lambda e: e["weight"], reverse=True)

    # Compute stats
    degrees = list(subject_degree.values())
    strengths = list(subject_strength.values())

    from datetime import datetime

    meta = {
        "generatedAt": datetime.now().isoformat(),
        "totalNodes": len(nodes),
        "totalEdges": len(edges),
        "supportedTypes": ["subject"],
        "weightMinConfigured": 1,
        "weightMinActual": min(data["weight"] for data in edge_weights.values()),
        "weightMax": max_weight,
        "degree": {
            "min": min(degrees),
            "max": max(degrees),
            "mean": round(sum(degrees) / len(degrees), 2) if degrees else 0,
        },
        "strength": {
            "min": min(strengths),
            "max": max(strengths),
            "mean": round(sum(strengths) / len(strengths), 2) if strengths else 0,
        },
        "topLabelCount": min(50, len(nodes)),
        "typePairs": [["subject", "subject"]],
        "labelPriorityTop": [
            nodes[i]["label"]
            for i in range(min(50, len(nodes)))
            if i < len(nodes)
        ],
    }

    return {"nodes": nodes, "edges": edges, "meta": meta}


def main():
    logger.info("=== Subject Co-occurrence Network Generator ===")

    # Load references dataset
    df = load_dataset_safe("references")
    if df is None:
        logger.error("Failed to load references dataset")
        sys.exit(1)

    records = df.to_dict("records")
    logger.info(f"Loaded {len(records)} reference records")

    # Generate network
    result = generate_subject_cooccurrence(records)

    # Save output
    output_path = OUTPUT_DIR / "subject-cooccurrence.json"
    save_json(result, output_path, minify=True)

    logger.info(
        f"Generated network: {result['meta']['totalNodes']} nodes, "
        f"{result['meta']['totalEdges']} edges"
    )
    logger.info("Done!")


if __name__ == "__main__":
    main()
