#!/usr/bin/env python3
"""
IWAC Scary Terms Co-occurrence Matrix Generator
Script to analyze co-occurrence of scary/radical terms in the Islam West Africa Collection dataset.
Generates data for co-occurrence matrix visualization.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from datetime import datetime
from collections import defaultdict
from itertools import combinations

try:
    from datasets import load_dataset
    import pandas as pd
except ImportError:
    print("Required packages not installed. Please run:")
    print("pip install datasets pandas huggingface-hub pyarrow")
    exit(1)


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class IWACCooccurrenceGenerator:
    """Generate co-occurrence matrix data from IWAC articles"""
    
    def __init__(self, output_dir: str = "static/data", window_size: int = 50):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.window_size = window_size  # Number of words for co-occurrence window
        
        # Define scary term families to search for (same as generate_scary_terms.py)
        self.scary_terms = {
            "radicalisation": ["radical", "radicaliser", "radicalisation", "radicalisme", "radicalisé", "radicalisée", "radicalisant", "radicalité"],
            "extrémisme": ["extrême", "extrémisme", "extrémiste", "extrémistes"],
            "intégrisme": ["intégrisme", "intégriste", "intégristes"],
            "fondamentalisme": ["fondamental", "fondamentale", "fondamentalisme", "fondamentaliste", "fondamentalistes"],
            "islamisme": ["islamisme", "islamiste", "islamistes"],
            "obscurantisme": ["obscurantisme", "obscurantiste", "obscurantistes"],
            "terrorisme": ["terrorisme", "terroriste", "terroristes"],
            "djihadisme": ["djihad", "djihadisme", "djihadiste", "djihadistes", "jihad", "jihadisme", "jihadiste", "jihadistes"],
            "salafisme": ["salaf", "salafisme", "salafiste", "salafistes"],
            "fanatisme": ["fanatique", "fanatisme", "fanatiser", "fanatisé", "fanatisée"],
            "endoctrinement": ["endoctriner", "endoctrinement", "endoctriné", "endoctrinée", "endoctrinés", "endoctrinées"],
            "wahhabisme": ["wahhabisme", "wahhabite", "wahhabites", "wahabia", "wahabite", "wahhâbisme"]
        }
        
        # Store dataset
        self.articles_df = None
        
    def fetch_articles_data(self) -> None:
        """Fetch articles from the IWAC dataset"""
        logger.info("Fetching articles from IWAC dataset...")
        
        dataset_name = "fmadore/islam-west-africa-collection"
        
        try:
            # Load articles subset
            logger.info("Loading articles subset...")
            dataset = load_dataset(dataset_name, "articles")
            
            # Convert to pandas DataFrame
            df = dataset['train'].to_pandas()
            logger.info(f"Loaded {len(df)} articles")
            
            self.articles_df = df.copy()
            
            # Clean and prepare data
            self._clean_data()
            
        except Exception as e:
            logger.error(f"Error loading articles data: {e}")
            raise
    
    def _clean_data(self) -> None:
        """Clean and prepare the data for analysis"""
        logger.info("Cleaning and preparing data...")
        
        # Remove rows without text data
        if 'lemma_text' in self.articles_df.columns:
            initial_count = len(self.articles_df)
            self.articles_df = self.articles_df.dropna(subset=['lemma_text'])
            self.articles_df = self.articles_df[self.articles_df['lemma_text'].str.strip() != '']
            logger.info(f"Removed {initial_count - len(self.articles_df)} articles without text data")
        
        # Clean country data
        if 'country' in self.articles_df.columns:
            self.articles_df['country'] = self.articles_df['country'].fillna('Unknown')
        
        # Parse and clean pub_date
        if 'pub_date' in self.articles_df.columns:
            self.articles_df['pub_date'] = pd.to_datetime(self.articles_df['pub_date'], errors='coerce')
            self.articles_df['year'] = self.articles_df['pub_date'].dt.year
            # Remove rows without valid year
            self.articles_df = self.articles_df.dropna(subset=['year'])
            self.articles_df['year'] = self.articles_df['year'].astype(int)
        
        logger.info(f"Final cleaned dataset: {len(self.articles_df)} articles")
    
    def find_term_positions(self, text: str) -> Dict[str, List[int]]:
        """Find all positions of each scary term family in the text"""
        if not text or not isinstance(text, str):
            return {}
        
        text_lower = text.lower()
        words = text_lower.split()
        
        term_positions: Dict[str, List[int]] = defaultdict(list)
        
        for term_family, variants in self.scary_terms.items():
            for i, word in enumerate(words):
                # Clean word of punctuation for matching
                clean_word = re.sub(r'[^\w\s]', '', word)
                if clean_word in [v.lower() for v in variants]:
                    term_positions[term_family].append(i)
        
        return dict(term_positions)
    
    def compute_cooccurrence_in_article(self, text: str) -> Dict[Tuple[str, str], int]:
        """Compute co-occurrences of scary terms in a single article using sliding window"""
        term_positions = self.find_term_positions(text)
        
        if len(term_positions) < 2:
            return {}
        
        cooccurrence_counts: Dict[Tuple[str, str], int] = defaultdict(int)
        
        # For each pair of different term families
        term_families = list(term_positions.keys())
        
        for i, term1 in enumerate(term_families):
            for term2 in term_families[i+1:]:
                # Check if any positions are within the window
                positions1 = term_positions[term1]
                positions2 = term_positions[term2]
                
                for pos1 in positions1:
                    for pos2 in positions2:
                        if abs(pos1 - pos2) <= self.window_size:
                            # Ensure consistent ordering (alphabetical)
                            pair = tuple(sorted([term1, term2]))
                            cooccurrence_counts[pair] += 1
        
        return dict(cooccurrence_counts)
    
    def generate_global_cooccurrence(self) -> Dict[str, Any]:
        """Generate global co-occurrence matrix across all articles"""
        logger.info("Generating global co-occurrence matrix...")
        
        if 'lemma_text' not in self.articles_df.columns:
            logger.error("Missing lemma_text column")
            return {}
        
        # Initialize co-occurrence matrix
        term_families = list(self.scary_terms.keys())
        cooccurrence_matrix: Dict[Tuple[str, str], int] = defaultdict(int)
        term_counts: Dict[str, int] = defaultdict(int)
        
        # Process each article
        total = len(self.articles_df)
        for idx, row in self.articles_df.iterrows():
            if idx % 1000 == 0:
                logger.info(f"Processing article {idx}/{total}...")
            
            text = row['lemma_text']
            
            # Get term positions to count individual terms
            term_positions = self.find_term_positions(text)
            for term, positions in term_positions.items():
                term_counts[term] += len(positions)
            
            # Compute co-occurrences
            article_cooccurrence = self.compute_cooccurrence_in_article(text)
            for pair, count in article_cooccurrence.items():
                cooccurrence_matrix[pair] += count
        
        # Build matrix in format suitable for D3.js
        matrix_data = self._build_matrix_data(term_families, cooccurrence_matrix, term_counts)
        
        return matrix_data
    
    def generate_country_cooccurrence(self) -> Dict[str, Any]:
        """Generate co-occurrence matrices by country"""
        logger.info("Generating country-wise co-occurrence matrices...")
        
        if 'country' not in self.articles_df.columns or 'lemma_text' not in self.articles_df.columns:
            logger.error("Missing required columns")
            return {}
        
        country_data = {}
        term_families = list(self.scary_terms.keys())
        
        # Group by country
        for country, country_df in self.articles_df.groupby('country'):
            if len(country_df) < 5:  # Skip countries with too few articles
                continue
            
            cooccurrence_matrix: Dict[Tuple[str, str], int] = defaultdict(int)
            term_counts: Dict[str, int] = defaultdict(int)
            
            for _, row in country_df.iterrows():
                text = row['lemma_text']
                
                # Get term positions to count individual terms
                term_positions = self.find_term_positions(text)
                for term, positions in term_positions.items():
                    term_counts[term] += len(positions)
                
                # Compute co-occurrences
                article_cooccurrence = self.compute_cooccurrence_in_article(text)
                for pair, count in article_cooccurrence.items():
                    cooccurrence_matrix[pair] += count
            
            # Build matrix data
            matrix_data = self._build_matrix_data(term_families, cooccurrence_matrix, term_counts)
            matrix_data['total_articles'] = len(country_df)
            country_data[country] = matrix_data
        
        logger.info(f"Generated co-occurrence data for {len(country_data)} countries")
        return country_data
    
    def _build_matrix_data(
        self, 
        term_families: List[str], 
        cooccurrence_matrix: Dict[Tuple[str, str], int],
        term_counts: Dict[str, int]
    ) -> Dict[str, Any]:
        """Build matrix data structure for D3.js visualization"""
        
        # Filter to terms that actually appear
        active_terms = sorted([t for t in term_families if term_counts.get(t, 0) > 0])
        
        if not active_terms:
            return {
                "terms": [],
                "matrix": [],
                "term_counts": {},
                "max_cooccurrence": 0
            }
        
        # Build square matrix
        n = len(active_terms)
        matrix = [[0] * n for _ in range(n)]
        
        # Fill matrix
        for i, term1 in enumerate(active_terms):
            for j, term2 in enumerate(active_terms):
                if i == j:
                    # Diagonal: term count
                    matrix[i][j] = term_counts.get(term1, 0)
                else:
                    # Off-diagonal: co-occurrence count
                    pair = tuple(sorted([term1, term2]))
                    matrix[i][j] = cooccurrence_matrix.get(pair, 0)
        
        # Find max co-occurrence value (excluding diagonal)
        max_cooccurrence = 0
        for i in range(n):
            for j in range(n):
                if i != j and matrix[i][j] > max_cooccurrence:
                    max_cooccurrence = matrix[i][j]
        
        return {
            "terms": active_terms,
            "matrix": matrix,
            "term_counts": {t: term_counts.get(t, 0) for t in active_terms},
            "max_cooccurrence": max_cooccurrence
        }
    
    def save_cooccurrence_data(self) -> None:
        """Generate and save all co-occurrence data to JSON files"""
        logger.info("Generating and saving co-occurrence data...")
        
        try:
            # Generate global co-occurrence
            global_data = self.generate_global_cooccurrence()
            global_path = self.output_dir / 'cooccurrence-global.json'
            with open(global_path, 'w', encoding='utf-8') as f:
                json.dump(global_data, f, ensure_ascii=False, separators=(',', ':'))
            logger.info(f"Saved global co-occurrence data to {global_path}")
            
            # Generate country co-occurrence
            country_data = self.generate_country_cooccurrence()
            country_path = self.output_dir / 'cooccurrence-countries.json'
            with open(country_path, 'w', encoding='utf-8') as f:
                json.dump(country_data, f, ensure_ascii=False, separators=(',', ':'))
            logger.info(f"Saved country co-occurrence data to {country_path}")
            
            # Save metadata
            metadata = {
                "generated_at": datetime.now().isoformat(),
                "total_articles": len(self.articles_df),
                "term_families": list(self.scary_terms.keys()),
                "term_families_count": len(self.scary_terms),
                "window_size": self.window_size,
                "countries": list(country_data.keys()),
                "data_structure": {
                    "global": "Co-occurrence matrix for all articles",
                    "countries": "Co-occurrence matrices grouped by country"
                },
                "matrix_description": "Square matrix where diagonal contains term counts and off-diagonal contains co-occurrence counts within window"
            }
            
            metadata_path = self.output_dir / 'cooccurrence-metadata.json'
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved metadata to {metadata_path}")
            
            # Also copy to build/data for production
            build_dir = self.output_dir.parent.parent / 'build' / 'data'
            if build_dir.exists():
                import shutil
                shutil.copy(global_path, build_dir / 'cooccurrence-global.json')
                shutil.copy(country_path, build_dir / 'cooccurrence-countries.json')
                shutil.copy(metadata_path, build_dir / 'cooccurrence-metadata.json')
                logger.info(f"Copied data files to {build_dir}")
            
        except Exception as e:
            logger.error(f"Error generating co-occurrence data: {e}")
            raise
    
    def process(self) -> None:
        """Main processing pipeline"""
        try:
            self.fetch_articles_data()
            self.save_cooccurrence_data()
            logger.info("✅ Co-occurrence data generation completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Co-occurrence data generation failed: {e}")
            raise


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate co-occurrence matrix data from IWAC articles')
    parser.add_argument('--output-dir', default='static/data', 
                       help='Output directory for JSON files (default: static/data)')
    parser.add_argument('--window-size', type=int, default=50,
                       help='Window size for co-occurrence detection (default: 50 words)')
    
    args = parser.parse_args()
    
    generator = IWACCooccurrenceGenerator(output_dir=args.output_dir, window_size=args.window_size)
    generator.process()


if __name__ == "__main__":
    main()
