#!/usr/bin/env python3
"""
IWAC Scary Terms Analysis Generator
Script to analyze scary/radical terms in the Islam West Africa Collection dataset.
Generates data for bar chart race visualization showing term usage over time.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict

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


class IWACScaryTermsGenerator:
    """Generate scary terms analysis data from IWAC articles"""
    
    def __init__(self, output_dir: str = "static/data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define scary term families to search for
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
    
    def count_term_occurrences(self, text: str, term_variants: List[str]) -> int:
        """Count occurrences of any variant of a term family in text (case-insensitive)"""
        if not text or not isinstance(text, str):
            return 0
        
        total_count = 0
        text_lower = text.lower()
        
        for variant in term_variants:
            # Use word boundaries to match whole words only
            pattern = r'\b' + re.escape(variant.lower()) + r'\b'
            matches = re.findall(pattern, text_lower)
            total_count += len(matches)
        
        return total_count
    
    def generate_temporal_data(self) -> Dict[str, Any]:
        """Generate scary terms data by year for bar chart race"""
        logger.info("Generating temporal scary terms data...")
        
        if 'year' not in self.articles_df.columns or 'lemma_text' not in self.articles_df.columns:
            logger.error("Missing required columns")
            return {}
        
        # Initialize results: year -> term -> count
        year_term_counts = defaultdict(lambda: defaultdict(int))
        
        # Process each article
        total = len(self.articles_df)
        for idx, row in self.articles_df.iterrows():
            if idx % 1000 == 0:
                logger.info(f"Processing article {idx}/{total}...")
            
            year = row['year']
            text = row['lemma_text']
            
            # Count occurrences of each scary term family
            for term_family, variants in self.scary_terms.items():
                count = self.count_term_occurrences(text, variants)
                if count > 0:
                    year_term_counts[year][term_family] += count
        
        # Convert to sorted structure for bar chart race
        temporal_data = {}
        for year in sorted(year_term_counts.keys()):
            term_counts = year_term_counts[year]
            # Sort by count and create list of [term, count] pairs
            sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
            temporal_data[str(year)] = {
                "year": int(year),
                "data": [[term, count] for term, count in sorted_terms]
            }
        
        logger.info(f"Generated temporal data for {len(temporal_data)} years")
        return temporal_data
    
    def generate_country_data(self) -> Dict[str, Any]:
        """Generate scary terms data by country"""
        logger.info("Generating country-wise scary terms data...")
        
        if 'country' not in self.articles_df.columns or 'lemma_text' not in self.articles_df.columns:
            logger.error("Missing required columns")
            return {}
        
        country_data = {}
        
        # Group by country
        for country, country_df in self.articles_df.groupby('country'):
            if len(country_df) < 5:  # Skip countries with too few articles
                continue
            
            term_counts = defaultdict(int)
            
            for _, row in country_df.iterrows():
                text = row['lemma_text']
                
                # Count occurrences of each scary term family
                for term_family, variants in self.scary_terms.items():
                    count = self.count_term_occurrences(text, variants)
                    if count > 0:
                        term_counts[term_family] += count
            
            if term_counts:
                sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
                country_data[country] = {
                    "country": country,
                    "total_articles": len(country_df),
                    "data": [[term, count] for term, count in sorted_terms]
                }
        
        logger.info(f"Generated data for {len(country_data)} countries")
        return country_data
    
    def generate_global_data(self) -> Dict[str, Any]:
        """Generate global scary terms summary"""
        logger.info("Generating global scary terms data...")
        
        term_counts = defaultdict(int)
        
        for _, row in self.articles_df.iterrows():
            text = row.get('lemma_text', '')
            
            # Count occurrences of each scary term family
            for term_family, variants in self.scary_terms.items():
                count = self.count_term_occurrences(text, variants)
                if count > 0:
                    term_counts[term_family] += count
        
        sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "total_articles": len(self.articles_df),
            "total_occurrences": sum(term_counts.values()),
            "data": [[term, count] for term, count in sorted_terms]
        }
    
    def save_scary_terms_data(self) -> None:
        """Generate and save all scary terms data to JSON files"""
        logger.info("Generating and saving scary terms data...")
        
        try:
            # Generate temporal data (for bar chart race)
            temporal_data = self.generate_temporal_data()
            temporal_path = self.output_dir / 'scary-terms-temporal.json'
            with open(temporal_path, 'w', encoding='utf-8') as f:
                json.dump(temporal_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved temporal data to {temporal_path}")
            
            # Generate country data
            country_data = self.generate_country_data()
            country_path = self.output_dir / 'scary-terms-countries.json'
            with open(country_path, 'w', encoding='utf-8') as f:
                json.dump(country_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved country data to {country_path}")
            
            # Generate global data
            global_data = self.generate_global_data()
            global_path = self.output_dir / 'scary-terms-global.json'
            with open(global_path, 'w', encoding='utf-8') as f:
                json.dump(global_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved global data to {global_path}")
            
            # Save metadata
            years = sorted([int(year) for year in temporal_data.keys()]) if temporal_data else []
            metadata = {
                "generated_at": datetime.now().isoformat(),
                "total_articles": len(self.articles_df),
                "term_families": list(self.scary_terms.keys()),
                "term_families_count": len(self.scary_terms),
                "total_variants": sum(len(variants) for variants in self.scary_terms.values()),
                "countries": list(country_data.keys()) if country_data else [],
                "year_range": [min(years), max(years)] if years else [],
                "data_structure": {
                    "temporal": "Scary term occurrences by year for bar chart race",
                    "countries": "Scary term occurrences grouped by country",
                    "global": "Overall scary term occurrences across all articles"
                },
                "term_definitions": {
                    term: variants for term, variants in self.scary_terms.items()
                }
            }
            
            metadata_path = self.output_dir / 'scary-terms-metadata.json'
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved metadata to {metadata_path}")
            
        except Exception as e:
            logger.error(f"Error generating scary terms data: {e}")
            raise
    
    def process(self) -> None:
        """Main processing pipeline"""
        try:
            self.fetch_articles_data()
            self.save_scary_terms_data()
            logger.info("✅ Scary terms data generation completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Scary terms data generation failed: {e}")
            raise


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate scary terms analysis data from IWAC articles')
    parser.add_argument('--output-dir', default='static/data', 
                       help='Output directory for JSON files (default: static/data)')
    
    args = parser.parse_args()
    
    generator = IWACScaryTermsGenerator(output_dir=args.output_dir)
    generator.process()


if __name__ == "__main__":
    main()
