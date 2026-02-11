#!/usr/bin/env python3
"""generate_topic_network.py
Generate topic network data for visualizing topic-article relationships.

This script creates network data where topics are central nodes and articles
are connected to them based on topic assignments.

INPUT:
    - static/data/topics/summary.json (topic metadata)
    - static/data/topics/{id}.json (individual topic files with articles)

OUTPUT:
    - static/data/networks/topic-network.json

The output includes:
    - nodes: topics (large central nodes) and articles (smaller peripheral nodes)
    - edges: connections between articles and their assigned topics (weighted by topic_prob)
    - meta: generation metadata and statistics
"""

from __future__ import annotations
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
from statistics import fmean

# ------------------ Configuration ------------------
DEFAULT_ARTICLES_PER_TOPIC = 50
MIN_TOPIC_PROB = 0.3

# ------------------ Paths ------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'static' / 'data'
TOPICS_DIR = DATA_DIR / 'topics'
OUT_DIR = DATA_DIR / 'networks'
OUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Build topic-article network")
    parser.add_argument(
        "--articles-per-topic",
        type=int,
        default=DEFAULT_ARTICLES_PER_TOPIC,
        help=f"Maximum articles per topic (default: {DEFAULT_ARTICLES_PER_TOPIC})"
    )
    parser.add_argument(
        "--min-prob",
        type=float,
        default=MIN_TOPIC_PROB,
        help=f"Minimum topic probability to include (default: {MIN_TOPIC_PROB})"
    )
    return parser.parse_args()


def load_topics_summary() -> List[Dict]:
    """Load topics summary data."""
    summary_file = TOPICS_DIR / 'summary.json'
    if not summary_file.exists():
        print(f"[ERROR] Topics summary file not found: {summary_file}")
        return []

    print(f"[INFO] Loading topics summary from {summary_file}")
    data = json.loads(summary_file.read_text(encoding='utf-8'))
    return data.get('topics', [])


def load_topic_details(topic_id: int) -> Optional[Dict]:
    """Load individual topic file with articles."""
    topic_file = TOPICS_DIR / f'{topic_id}.json'
    if not topic_file.exists():
        return None

    return json.loads(topic_file.read_text(encoding='utf-8'))


def extract_keywords(label: str) -> List[str]:
    """Extract keywords from topic label.

    Topic labels are in format: "Keyword1 - Keyword2 - Keyword3 - ..."
    Underscore-joined phrases (e.g. côte_ivoire) are converted to spaces.
    """
    if not label or label == 'Outlier':
        return []

    keywords = [kw.strip().replace('_', ' ') for kw in label.split(' - ') if kw.strip()]
    return keywords[:5]  # Limit to first 5 keywords


def build_topic_network(args):
    """Build the topic-article network."""

    print("Building topic network...")

    # Load topics summary
    topics_summary = load_topics_summary()
    if not topics_summary:
        print("[ERROR] No topics found")
        return

    print(f"[INFO] Found {len(topics_summary)} topics")

    nodes = []
    edges = []

    # Track unique articles to avoid duplicates
    article_ids = set()

    topic_nodes_count = 0
    article_nodes_count = 0
    total_edges = 0
    all_probs = []

    # Process each topic (excluding outlier topic with id=-1)
    for topic_summary in topics_summary:
        topic_id = topic_summary.get('id')

        # Skip outlier topic
        if topic_id == -1:
            print(f"  [SKIP] Outlier topic (id=-1) with {topic_summary.get('count', 0)} docs")
            continue

        topic_label = topic_summary.get('label', f'Topic {topic_id}')
        topic_count = topic_summary.get('count', 0)

        # Load detailed topic data
        topic_details = load_topic_details(topic_id)
        if not topic_details:
            print(f"  [WARN] Could not load details for topic {topic_id}")
            continue

        # Extract keywords from label
        keywords = extract_keywords(topic_label)

        # Create topic node
        topic_node_id = f"topic:{topic_id}"
        topic_node = {
            'id': topic_node_id,
            'type': 'topic',
            'label': topic_label,
            'count': topic_count,
            'keywords': keywords,
            'degree': 0,
            'strength': 0,
            'labelPriority': 1  # Topics have high label priority
        }
        nodes.append(topic_node)
        topic_nodes_count += 1

        # Get articles for this topic
        docs = topic_details.get('docs', [])

        # Sort by topic_prob (descending) and take top N
        docs_sorted = sorted(
            docs,
            key=lambda d: d.get('topic_prob', 0),
            reverse=True
        )[:args.articles_per_topic]

        # Process articles
        for doc in docs_sorted:
            topic_prob = doc.get('topic_prob', 0)

            # Skip articles with low probability
            if topic_prob < args.min_prob:
                continue

            # Get article URL as unique identifier
            url = doc.get('url', '')
            if not url:
                continue

            # Create article node ID from URL
            article_id = f"article:{url.split('/')[-1]}" if '/' in url else f"article:{hash(url)}"

            # Only add article node once (in case of multiple topics)
            if article_id not in article_ids:
                article_ids.add(article_id)

                article_node = {
                    'id': article_id,
                    'type': 'article',
                    'label': doc.get('title', 'Untitled'),
                    'topicProb': round(topic_prob, 4),
                    'country': doc.get('country', ''),
                    'newspaper': doc.get('newspaper', ''),
                    'pubDate': doc.get('pub_date', ''),
                    'url': url,
                    'topicId': topic_id,
                    'degree': 1,  # Connected to one topic
                    'strength': round(topic_prob, 4),
                    'labelPriority': 0  # Articles have lower label priority
                }
                nodes.append(article_node)
                article_nodes_count += 1

            # Create edge from article to topic
            all_probs.append(topic_prob)
            edge = {
                'source': topic_node_id,
                'target': article_id,
                'weight': round(topic_prob, 4),
                'weightNorm': 0  # Will be normalized later
            }
            edges.append(edge)
            total_edges += 1

            # Update topic node degree and strength
            topic_node['degree'] += 1
            topic_node['strength'] += topic_prob

        # Round topic strength
        topic_node['strength'] = round(topic_node['strength'], 2)

        print(f"  [OK] Topic {topic_id}: {topic_node['degree']} articles")

    # Normalize edge weights
    if edges:
        max_weight = max(e['weight'] for e in edges)
        min_weight = min(e['weight'] for e in edges)
        for edge in edges:
            if max_weight > min_weight:
                edge['weightNorm'] = round(
                    (edge['weight'] - min_weight) / (max_weight - min_weight),
                    4
                )
            else:
                edge['weightNorm'] = 1.0

    print(f"\nNetwork Statistics:")
    print(f"   - Topic nodes: {topic_nodes_count}")
    print(f"   - Article nodes: {article_nodes_count}")
    print(f"   - Total nodes: {len(nodes)}")
    print(f"   - Total edges: {total_edges}")

    avg_prob = fmean(all_probs) if all_probs else 0

    # Prepare output
    output = {
        'nodes': nodes,
        'edges': edges,
        'meta': {
            'generatedAt': datetime.now(timezone.utc).isoformat(),
            'totalNodes': len(nodes),
            'totalTopics': topic_nodes_count,
            'totalArticles': article_nodes_count,
            'totalEdges': total_edges,
            'articlesPerTopic': args.articles_per_topic,
            'minTopicProb': args.min_prob,
            'avgTopicProb': round(avg_prob, 4),
            'weightMin': round(min(all_probs), 4) if all_probs else 0,
            'weightMax': round(max(all_probs), 4) if all_probs else 1
        }
    }

    # Save output
    output_file = OUT_DIR / 'topic-network.json'
    output_file.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

    print(f"\n[DONE] Topic network saved to {output_file}")
    print(f"   Average topic probability: {avg_prob:.2%}")


if __name__ == "__main__":
    args = parse_args()
    build_topic_network(args)
