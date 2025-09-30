#!/usr/bin/env python3
"""
generate_overview_stats.py
===========================

Génère les statistiques globales pour le tableau de bord IWAC.
Calcule les métriques clés : total d'items, pays, langues, types,
ainsi que des statistiques détaillées par dataset.

Le script charge les datasets IWAC depuis le Hub Hugging Face et produit
un fichier JSON avec toutes les statistiques nécessaires pour la page overview.

Usage
-----
    python generate_overview_stats.py [--repo MON_USER/MON_DATASET] [--output-dir OUTPUT_DIR]

Exemple:
    python generate_overview_stats.py --repo fmadore/islam-west-africa-collection --output-dir static/data

Variables d'environnement
-------------------------
HF_TOKEN   Jeton d'accès personnel pour le Hugging Face Hub
"""
import argparse
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from datasets import load_dataset
from huggingface_hub import HfFolder, login
import pandas as pd


def configure_logging() -> None:
    """Configure le logging de base."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def safe_sum_column(df: pd.DataFrame, column_name: str) -> int:
    """
    Calcule la somme d'une colonne en gérant les valeurs manquantes et les types.
    
    Args:
        df: DataFrame à analyser
        column_name: Nom de la colonne à sommer
    
    Returns:
        Somme des valeurs valides de la colonne
    """
    if column_name not in df.columns:
        return 0
    
    values = pd.to_numeric(df[column_name], errors='coerce').fillna(0)
    return int(values.sum())


def count_non_empty_rows(df: pd.DataFrame, column_name: str) -> int:
    """
    Compte le nombre de lignes non vides pour une colonne donnée.
    
    Args:
        df: DataFrame à analyser
        column_name: Nom de la colonne à analyser
    
    Returns:
        Nombre de lignes avec des valeurs non vides
    """
    if column_name not in df.columns:
        return 0
    
    non_empty = df[column_name].notna() & (df[column_name] != "") & (df[column_name] != 0)
    return int(non_empty.sum())


def load_dataset_safe(repo_id: str, config_name: str, token: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Charge un dataset de manière sécurisée avec gestion d'erreurs.
    
    Args:
        repo_id: ID du repository Hugging Face
        config_name: Nom de la configuration
        token: Token d'authentification
    
    Returns:
        DataFrame du dataset ou None en cas d'erreur
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Chargement du dataset '{repo_id}', configuration '{config_name}'...")
        ds = load_dataset(
            repo_id, 
            name=config_name, 
            split="train", 
            token=token
        )
        df = ds.to_pandas()
        logger.info(f"Dataset '{config_name}' chargé: {len(df)} lignes")
        return df
    except Exception as e:
        logger.warning(f"Impossible de charger le dataset '{config_name}': {e}")
        return None


def parse_iso8601_duration_to_minutes(val: str) -> int:
    """
    Convertit une durée ISO8601 (ex: PT208M, PT2H30M, PT3600S) en minutes.
    
    Args:
        val: Durée au format ISO8601
    
    Returns:
        Durée en minutes entières
    """
    if not isinstance(val, str) or not val or not val.startswith('P'):
        return 0
    
    pattern = re.compile(
        r"P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?"
    )
    m = pattern.fullmatch(val.strip())
    
    if not m:
        simple = re.match(r"PT(\d+)M", val.strip())
        if simple:
            return int(simple.group(1))
        return 0
    
    days = int(m.group('days') or 0)
    hours = int(m.group('hours') or 0)
    minutes = int(m.group('minutes') or 0)
    seconds = int(m.group('seconds') or 0)
    
    total_minutes = days * 24 * 60 + hours * 60 + minutes + seconds / 60.0
    return int(round(total_minutes))


def get_unique_values(df: pd.DataFrame, column_name: str) -> List[str]:
    """
    Récupère les valeurs uniques d'une colonne, en filtrant les valeurs vides.
    
    Args:
        df: DataFrame à analyser
        column_name: Nom de la colonne
    
    Returns:
        Liste des valeurs uniques non vides
    """
    if df is None or column_name not in df.columns:
        return []
    
    values = df[column_name].dropna()
    values = values[values != ""]
    return sorted(values.unique().tolist())


def calculate_dataset_stats(df: pd.DataFrame, dataset_name: str) -> Dict[str, Any]:
    """
    Calcule les statistiques pour un dataset donné.
    
    Args:
        df: DataFrame à analyser
        dataset_name: Nom du dataset
    
    Returns:
        Dictionnaire avec les statistiques
    """
    logger = logging.getLogger(__name__)
    
    if df is None or df.empty:
        logger.warning(f"Dataset '{dataset_name}' vide ou non disponible")
        return {
            "total_records": 0,
            "total_words": 0,
            "total_pages": 0,
            "records_with_word_count": 0,
            "records_with_page_count": 0,
            "records_with_ocr": 0
        }
    
    word_count_col = "nb_mots"
    page_count_col = "nb_pages"
    
    total_records = len(df)
    total_words = safe_sum_column(df, word_count_col)
    total_pages = safe_sum_column(df, page_count_col)
    
    stats = {
        "total_records": total_records,
        "total_words": total_words,
        "total_pages": total_pages,
        "records_with_word_count": count_non_empty_rows(df, word_count_col),
        "records_with_page_count": count_non_empty_rows(df, page_count_col),
        "records_with_ocr": count_non_empty_rows(df, "OCR")
    }
    
    # Statistiques spécifiques pour l'audiovisuel
    if dataset_name == "audiovisual":
        duration_series = df.get('extent', pd.Series(dtype=str)).fillna('').astype(str)
        duration_minutes = duration_series.map(parse_iso8601_duration_to_minutes)
        
        total_duration = int(duration_minutes.sum())
        records_with_duration = int((df.get('extent', pd.Series(dtype=str)).fillna('') != '').sum())
        
        stats.update({
            "total_duration_minutes": total_duration,
            "records_with_duration": records_with_duration,
            "average_duration_minutes": int(round(total_duration / records_with_duration)) if records_with_duration > 0 else 0
        })
    
    logger.info(f"  {dataset_name}: {total_records:,} enregistrements, {total_words:,} mots, {total_pages:,} pages")
    
    return stats


def calculate_overview_stats(repo_id: str, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Calcule toutes les statistiques overview pour le dashboard.
    
    Args:
        repo_id: ID du repository Hugging Face
        token: Token d'authentification
    
    Returns:
        Dictionnaire complet avec toutes les statistiques
    """
    logger = logging.getLogger(__name__)
    
    configs = ["articles", "publications", "documents", "audiovisual"]
    
    # Structure de données pour les résultats
    overview_stats = {
        "metadata": {
            "repository": repo_id,
            "generated_at": datetime.now().isoformat(),
            "script_version": "1.0"
        },
        "summary": {
            "total_items": 0,
            "total_words": 0,
            "total_pages": 0,
            "total_duration_minutes": 0,
            "countries": 0,
            "languages": 0,
            "types": 0,
            "newspapers": 0
        },
        "by_dataset": {},
        "by_country": {},
        "by_language": {},
        "by_type": {},
        "recent_items": []
    }
    
    # Collecteurs globaux
    all_countries = set()
    all_languages = set()
    all_types = set()
    all_newspapers = set()
    all_items = []
    
    # Traiter chaque dataset
    for config in configs:
        logger.info(f"\nTraitement de '{config}'...")
        
        df = load_dataset_safe(repo_id, config, token)
        
        if df is None or df.empty:
            continue
        
        # Statistiques du dataset
        dataset_stats = calculate_dataset_stats(df, config)
        overview_stats["by_dataset"][config] = dataset_stats
        
        # Ajouter aux totaux
        overview_stats["summary"]["total_items"] += dataset_stats["total_records"]
        overview_stats["summary"]["total_words"] += dataset_stats["total_words"]
        overview_stats["summary"]["total_pages"] += dataset_stats["total_pages"]
        
        if "total_duration_minutes" in dataset_stats:
            overview_stats["summary"]["total_duration_minutes"] += dataset_stats["total_duration_minutes"]
        
        # Collecter les valeurs uniques
        countries = get_unique_values(df, "country")
        languages = get_unique_values(df, "language")
        types = get_unique_values(df, "type")
        
        all_countries.update(countries)
        all_languages.update(languages)
        all_types.update(config)  # Le type de dataset lui-même
        
        # Collecter les journaux (pour articles et publications)
        if config in ["articles", "publications"]:
            newspapers = get_unique_values(df, "newspaper")
            all_newspapers.update(newspapers)
        
        # Statistiques par pays
        for country in countries:
            if country not in overview_stats["by_country"]:
                overview_stats["by_country"][country] = {
                    "total_records": 0,
                    "by_dataset": {}
                }
            
            country_df = df[df["country"] == country]
            overview_stats["by_country"][country]["total_records"] += len(country_df)
            overview_stats["by_country"][country]["by_dataset"][config] = len(country_df)
        
        # Statistiques par langue
        for language in languages:
            if language not in overview_stats["by_language"]:
                overview_stats["by_language"][language] = {
                    "total_records": 0,
                    "by_dataset": {}
                }
            
            lang_df = df[df["language"] == language]
            overview_stats["by_language"][language]["total_records"] += len(lang_df)
            overview_stats["by_language"][language]["by_dataset"][config] = len(lang_df)
        
        # Collecter des items récents (si date disponible)
        if "created_date" in df.columns:
            for _, row in df.head(5).iterrows():
                all_items.append({
                    "title": str(row.get("title", "Sans titre")),
                    "country": str(row.get("country", "N/A")),
                    "language": str(row.get("language", "N/A")),
                    "type": config,
                    "created_date": str(row.get("created_date", ""))
                })
    
    # Statistiques par type
    for config in configs:
        if config in overview_stats["by_dataset"]:
            overview_stats["by_type"][config] = {
                "total_records": overview_stats["by_dataset"][config]["total_records"]
            }
    
    # Finaliser les totaux
    overview_stats["summary"]["countries"] = len(all_countries)
    overview_stats["summary"]["languages"] = len(all_languages)
    overview_stats["summary"]["types"] = len([t for t in configs if t in overview_stats["by_dataset"]])
    overview_stats["summary"]["newspapers"] = len(all_newspapers)
    
    # Ajouter les listes de valeurs uniques
    overview_stats["summary"]["country_list"] = sorted(all_countries)
    overview_stats["summary"]["language_list"] = sorted(all_languages)
    overview_stats["summary"]["type_list"] = sorted([t for t in configs if t in overview_stats["by_dataset"]])
    
    # Trier et limiter les items récents
    all_items.sort(key=lambda x: x["created_date"], reverse=True)
    overview_stats["recent_items"] = all_items[:10]
    
    # Calculer des pourcentages de couverture
    total = overview_stats["summary"]["total_items"]
    if total > 0:
        total_with_words = sum(
            ds.get("records_with_word_count", 0) 
            for ds in overview_stats["by_dataset"].values()
        )
        total_with_pages = sum(
            ds.get("records_with_page_count", 0) 
            for ds in overview_stats["by_dataset"].values()
        )
        total_with_ocr = sum(
            ds.get("records_with_ocr", 0) 
            for ds in overview_stats["by_dataset"].values()
        )
        
        overview_stats["summary"]["word_count_coverage_percent"] = round((total_with_words / total) * 100, 2)
        overview_stats["summary"]["page_count_coverage_percent"] = round((total_with_pages / total) * 100, 2)
        overview_stats["summary"]["ocr_coverage_percent"] = round((total_with_ocr / total) * 100, 2)
    
    logger.info(f"\n{'='*50}")
    logger.info("STATISTIQUES GLOBALES")
    logger.info(f"{'='*50}")
    logger.info(f"Total d'items: {overview_stats['summary']['total_items']:,}")
    logger.info(f"Pays: {overview_stats['summary']['countries']}")
    logger.info(f"Langues: {overview_stats['summary']['languages']}")
    logger.info(f"Types: {overview_stats['summary']['types']}")
    logger.info(f"Journaux: {overview_stats['summary']['newspapers']}")
    logger.info(f"Mots totaux: {overview_stats['summary']['total_words']:,}")
    logger.info(f"Pages totales: {overview_stats['summary']['total_pages']:,}")
    
    return overview_stats


def save_json(data: Any, path: Path) -> None:
    """Save data as JSON file."""
    logger = logging.getLogger(__name__)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    try:
        abs_path = path.resolve()
        cwd = Path.cwd().resolve()
        display = abs_path.relative_to(cwd)
    except Exception:
        display = path
    
    logger.info(f"Wrote {display}")


def main():
    configure_logging()
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(
        description="Génère les statistiques overview pour le dashboard IWAC."
    )
    parser.add_argument(
        "--repo",
        default="fmadore/islam-west-africa-collection",
        help="ID du repository sur le Hugging Face Hub"
    )
    parser.add_argument(
        "--output-dir",
        default="static/data",
        help="Répertoire de sortie pour le fichier JSON"
    )
    
    args = parser.parse_args()
    
    repo_id = args.repo
    output_dir = Path(args.output_dir)
    
    # Authentification avec le Hub
    token = os.getenv("HF_TOKEN") or HfFolder.get_token()
    if not token:
        logger.info("Token Hugging Face non trouvé. Tentative de connexion interactive.")
        try:
            login()
            token = HfFolder.get_token()
        except Exception as e:
            logger.error(f"Échec de la connexion au Hugging Face Hub: {e}")
            return
    
    # Calculer les statistiques
    overview_stats = calculate_overview_stats(repo_id, token)
    
    # Sauvegarder le fichier JSON
    save_json(overview_stats, output_dir / "overview-stats.json")
    
    logger.info("✅ Overview statistics generation completed successfully!")


if __name__ == "__main__":
    main()
