#!/usr/bin/env python3
"""
Build compact, static JSON for the Topic Explorer UI.

Default output: the SvelteKit static data folder (sveltekit-app/static/data)
- summary.json
- topics/{topic_id}.json

This runs locally, loads the HF dataset (articles or publications), and exports
only the fields the static UI needs. No server or DB required.
"""
import argparse
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from datasets import load_dataset


def month_key(date_str: str) -> str:
    if not date_str:
        return ""
    # Try multiple formats conservatively
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%Y-%m", "%Y"):
        try:
            dt = datetime.strptime(date_str[:10], fmt) if len(date_str) >= 7 else datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m")
        except Exception:
            continue
    # Fallback: attempt to slice year-month
    if len(date_str) >= 7 and date_str[4] in ("-", "/"):
        return date_str[:7].replace('/', '-')
    return ""


def safe_str(x: Any) -> str:
    return "" if x is None else str(x)


def clean_topic_label(label: str) -> str:
    """
    Clean topic labels for display.

    LDA labels are already formatted as "Word1 - Word2 - Word3" and only
    need whitespace normalisation.  Legacy BERTopic labels like
    "91_pouytenga_sécurité_faib" are still handled for backwards
    compatibility.
    """
    if not label:
        return label

    stripped = label.strip()

    # LDA labels: already in "Word - Word" format
    # Phrases joined by underscores (e.g. côte_ivoire, président_république)
    # are converted to spaces for display.
    if " - " in stripped and not re.match(r'^\d+_', stripped):
        parts = [part.strip().replace('_', ' ') for part in stripped.split(' - ') if part.strip()]
        return ' - '.join(parts)

    # Legacy BERTopic format: "91_pouytenga_sécurité_faib_tenue"
    cleaned = re.sub(r'^\d+_', '', stripped)
    parts = [p.strip() for p in cleaned.split('_') if p and p.strip()]

    def cap_words(s: str) -> str:
        normalized = ' '.join(s.split())
        return ' '.join(
            (w[0].upper() + w[1:].lower()) if len(w) > 1 else w.upper()
            for w in normalized.split(' ')
            if w
        )

    return ' - '.join(cap_words(p) for p in parts)


def main():
    parser = argparse.ArgumentParser(description="Export static JSON for Topic Explorer")
    # Default to static/data/topics in the project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    default_out_dir = project_root / "static" / "data" / "topics"
    parser.add_argument("--repo", default="fmadore/islam-west-africa-collection")
    parser.add_argument("--config-name", choices=["articles", "publications"], default="articles")
    parser.add_argument("--output-dir", default=str(default_out_dir), help=f"Output directory (default: {default_out_dir})")
    parser.add_argument("--max-docs", type=int, default=0, help="Limit number of docs (0 = all)")
    parser.add_argument("--per-topic-docs", type=int, default=200, help="Max docs per topic to include")
    parser.add_argument("--topic-min-count", type=int, default=5, help="Drop topics with < count")

    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    topics_dir = out_dir
    # Note: out_dir is already the topics folder, so we don't need to append "topics" again

    # Use HF_TOKEN environment variable directly
    token = os.getenv("HF_TOKEN")

    print(f"Loading HF dataset {args.repo} · config={args.config_name}…")
    ds = load_dataset(args.repo, name=args.config_name, split="train", token=token)
    df = ds.to_pandas()
    if args.max_docs and len(df) > args.max_docs:
        df = df.head(args.max_docs)

    # ── Map LDA columns to the generic names used downstream ──────────
    lda_renames = {
        "lda_topic_id": "topic_id",
        "lda_topic_prob": "topic_prob",
        "lda_topic_label": "topic_label",
    }
    present_lda = {k: v for k, v in lda_renames.items() if k in df.columns}
    if present_lda:
        # Drop old BERTopic columns to avoid duplicates after rename
        old_cols = [v for v in present_lda.values() if v in df.columns]
        if old_cols:
            df = df.drop(columns=old_cols)
            print(f"Dropped old columns: {old_cols}")
        df = df.rename(columns=present_lda)
        print(f"Mapped LDA columns: {present_lda}")

    # Expected columns (some may be missing depending on pipeline stage)
    maybe_cols = {
        "topic_id", "topic_prob", "topic_label", "pub_date", "date", "country",
        "newspaper", "source", "title", "ocr_title", "url", "source_url", "o:source",
        "sentiment_label", "sentiment_score",
        # AI fields (either gemini_* or chatgpt_*)
        "gemini_polarite", "chatgpt_polarite",
    }
    for c in list(maybe_cols):
        if c not in df.columns:
            # Add empty column for simplicity
            df[c] = None

    # Determine which AI family exists
    ai_prefix = None
    for prefix in ("gemini", "chatgpt"):
        if any(col.startswith(prefix + "_") for col in df.columns):
            ai_prefix = prefix
            break
    ai_fields = []
    if ai_prefix:
        ai_fields = [c for c in df.columns if c.startswith(ai_prefix + "_")]

    # Keep only needed fields for documents
    doc_fields = [
        "topic_id", "topic_prob", "topic_label",
        "pub_date", "date", "country", "newspaper", "source",
        "title", "ocr_title", "url", "source_url", "o:source",
        "sentiment_label", "sentiment_score",
    ] + ai_fields
    df_docs = df[doc_fields].copy()

    # Normalize date: prefer pub_date, fallback to date
    df_docs["_month"] = df_docs["pub_date"].fillna(df_docs["date"]).map(month_key)

    # Drop rows without a topic_id
    if "topic_id" not in df_docs.columns:
        raise SystemExit("The dataset does not include 'topic_id' (or 'lda_topic_id'). Run the LDA topic modeling pipeline first.")
    df_docs = df_docs[df_docs["topic_id"].notnull()]

    # Summary aggregates
    topic_counts = df_docs["topic_id"].value_counts().to_dict()
    unique_topics = len(topic_counts)
    total_docs = int(df_docs.shape[0])

    topics_summary: List[Dict[str, Any]] = []
    for tid, cnt in sorted(topic_counts.items(), key=lambda x: (-x[1], x[0])):
        if cnt < args.topic_min_count:
            continue
        # label: use mode of topic_label for this topic
        labels = df_docs.loc[df_docs["topic_id"] == tid, "topic_label"].dropna().astype(str)
        raw_label = labels.mode().iloc[0] if not labels.empty else f"Topic {tid}"
        # Clean the topic label for better readability
        clean_label = clean_topic_label(raw_label)
        topics_summary.append({"id": int(tid), "label": clean_label, "count": int(cnt)})

    summary = {
        "total_docs": total_docs,
        "unique_topics": unique_topics,
        "topics": topics_summary,
        "ai_fields": ai_fields,
    }

    with open(out_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out_dir / 'summary.json'}")

    # Per-topic files
    for item in topics_summary:
        tid = item["id"]
        sub = df_docs[df_docs["topic_id"] == tid].copy()
        sub = sub.sort_values(by=["topic_prob"], ascending=False).head(args.per_topic_docs)

        # counts by country
        counts_by_country = Counter([safe_str(c) for c in sub["country"].fillna("") if safe_str(c)])
        # counts by month
        counts_by_month = Counter([m for m in sub["_month"].fillna("") if m])
        # avg prob
        avg_prob = float(pd.to_numeric(sub["topic_prob"], errors="coerce").fillna(0).mean()) if "topic_prob" in sub else 0.0

        # docs
        docs = []
        keep_cols = [c for c in doc_fields if c in sub.columns]
        for _, row in sub.iterrows():
            d = {c: (None if pd.isna(row[c]) else row[c]) for c in keep_cols}
            # Clean underscore-joined phrases in per-document topic labels
            if d.get("topic_label"):
                d["topic_label"] = d["topic_label"].replace('_', ' ')
            docs.append(d)

        topic_blob = {
            "id": tid,
            "label": item["label"],
            "count": item["count"],
            "avg_prob": avg_prob,
            "counts_by_country": dict(counts_by_country),
            "counts_by_month": dict(counts_by_month),
            "ai_fields": ai_fields,
            "docs": docs,
        }

        path = out_dir / f"{tid}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(topic_blob, f, ensure_ascii=False, indent=2)
        # print each file path briefly
        print(f"Wrote {path}")

    print(f"Done. Data written to: {out_dir}")


if __name__ == "__main__":
    main()
