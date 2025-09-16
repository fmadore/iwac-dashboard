#!/usr/bin/env python3
"""
IWAC Wordcloud Data Generator
Script to extract word frequency data from French articles in the IWAC dataset
for creating interactive wordcloud visualizations
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime
from collections import Counter, defaultdict

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


class IWACWordcloudGenerator:
    """Generate wordcloud data from French articles in IWAC dataset"""
    
    def __init__(self, output_dir: str = "static/data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Words to exclude (common stop words not already filtered)
        self.exclude_words = {
            'être', 'avoir', 'faire', 'dire', 'aller', 'voir', 'savoir', 'prendre',
            'venir', 'falloir', 'vouloir', 'pouvoir', 'premier', 'grand', 'petit',
            'nouveau', 'dernier', 'bon', 'français', 'public', 'même', 'tout',
            'autre', 'temps', 'personne', 'année', 'jour', 'main', 'chose',
            'moment', 'pays', 'fois', 'partie', 'cas', 'problème', 'lieu',
            'système', 'état', 'programme', 'question', 'groupe', 'fin',
            'société', 'fait', 'politique', 'point', 'niveau', 'ordre',
            'développement', 'action', 'mesure', 'moyen', 'service', 'projet',
            'forme', 'rapport', 'place', 'recherche', 'cadre', 'travail',
            'million', 'milliard', 'pourcentage', 'exemple', 'nombre', 'type',
            'sorte', 'espèce', 'genre', 'manière', 'façon', 'plus', 'moins',
            'très', 'bien', 'encore', 'aussi', 'déjà', 'toujours', 'jamais',
            'souvent', 'parfois', 'quelquefois', 'ailleurs', 'partout', 'quelque',
            'plusieurs', 'certains', 'autres', 'tous', 'toutes', 'chaque',
            'tels', 'telles', 'tel', 'telle', 'ces', 'cette', 'cet', 'celui',
            'celle', 'ceux', 'celles', 'lequel', 'laquelle', 'lesquels',
            'lesquelles', 'dont', 'où', 'quand', 'comment', 'pourquoi',
            'parce', 'puisque', 'comme', 'alors', 'donc', 'ainsi', 'cependant',
            'toutefois', 'néanmoins', 'pourtant', 'mais', 'or', 'car', 'si',
            'selon', 'suivant', 'malgré', 'grâce', 'cause', 'suite', 'cours',
            'pendant', 'durant', 'avant', 'après', 'depuis', 'jusqu', 'vers',
            'chez', 'sous', 'sur', 'dans', 'pour', 'par', 'avec', 'sans',
            'contre', 'entre', 'parmi', 'auprès', 'près', 'loin', 'autour',
            'puis', 'ensuite', 'enfin', 'bref', 'donc', 'ainsi', 'alors'
        }
        
        # Minimum word length
        self.min_word_length = 3
        
        # Minimum frequency threshold
        self.min_frequency = 2
        
        # Store dataset
        self.articles_df = None
        
    def fetch_articles_data(self) -> None:
        """Fetch French articles from the IWAC dataset"""
        logger.info("Fetching French articles from IWAC dataset...")
        
        dataset_name = "fmadore/islam-west-africa-collection"
        
        try:
            # Load only the articles subset
            logger.info("Loading articles subset...")
            dataset = load_dataset(dataset_name, "articles")
            
            # Convert to pandas DataFrame
            df = dataset['train'].to_pandas()
            logger.info(f"Loaded {len(df)} articles")
            
            # Filter for French language only
            if 'language' in df.columns:
                french_mask = df['language'] == 'Français'
                self.articles_df = df[french_mask].copy()
                logger.info(f"Filtered to {len(self.articles_df)} French articles")
            else:
                logger.warning("No 'language' column found, using all articles")
                self.articles_df = df.copy()
            
            # Check required columns
            required_columns = ['country', 'lemma_nostop', 'pub_date']
            missing_columns = [col for col in required_columns if col not in self.articles_df.columns]
            
            if missing_columns:
                logger.warning(f"Missing columns: {missing_columns}")
                logger.info(f"Available columns: {list(self.articles_df.columns)}")
            
            # Clean and prepare data
            self._clean_data()
            
        except Exception as e:
            logger.error(f"Error loading articles data: {e}")
            raise
    
    def _clean_data(self) -> None:
        """Clean and prepare the data for analysis"""
        logger.info("Cleaning and preparing data...")
        
        # Remove rows without lemma_nostop data
        if 'lemma_nostop' in self.articles_df.columns:
            initial_count = len(self.articles_df)
            self.articles_df = self.articles_df.dropna(subset=['lemma_nostop'])
            self.articles_df = self.articles_df[self.articles_df['lemma_nostop'].str.strip() != '']
            logger.info(f"Removed {initial_count - len(self.articles_df)} articles without lemma data")
        
        # Clean country data
        if 'country' in self.articles_df.columns:
            self.articles_df['country'] = self.articles_df['country'].fillna('Unknown')
        
        # Parse and clean pub_date
        if 'pub_date' in self.articles_df.columns:
            self.articles_df['pub_date'] = pd.to_datetime(self.articles_df['pub_date'], errors='coerce')
            # Add year column for temporal analysis
            self.articles_df['year'] = self.articles_df['pub_date'].dt.year
        
        logger.info(f"Final cleaned dataset: {len(self.articles_df)} articles")
    
    def _extract_words(self, lemma_text: str) -> List[str]:
        """Extract and filter words from lemma_nostop text"""
        if pd.isna(lemma_text) or not isinstance(lemma_text, str):
            return []
        
        # Split by whitespace and clean
        words = lemma_text.lower().split()
        
        # Filter words
        filtered_words = []
        for word in words:
            # Remove punctuation and numbers
            word = re.sub(r'[^\w]', '', word)
            
            # Skip if too short, contains numbers, or is in exclude list
            if (len(word) >= self.min_word_length and 
                not re.search(r'\d', word) and 
                word not in self.exclude_words):
                filtered_words.append(word)
        
        return filtered_words
    
    def generate_global_wordcloud_data(self) -> Dict[str, Any]:
        """Generate global word frequency data"""
        logger.info("Generating global wordcloud data...")
        
        word_counter = Counter()
        
        for _, row in self.articles_df.iterrows():
            if 'lemma_nostop' in row:
                words = self._extract_words(row['lemma_nostop'])
                word_counter.update(words)
        
        # Filter by minimum frequency and get top words
        filtered_words = {word: count for word, count in word_counter.items() 
                         if count >= self.min_frequency}
        
        # Sort by frequency and take top 200 words
        top_words = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:200]
        
        # Convert to wordcloud2.js format: [['word', weight], ...]
        wordcloud_data = [[word, count] for word, count in top_words]
        
        logger.info(f"Generated global wordcloud with {len(wordcloud_data)} words")
        return {
            "data": wordcloud_data,
            "total_articles": len(self.articles_df),
            "total_words": sum(word_counter.values()),
            "unique_words": len(word_counter)
        }
    
    def generate_country_wordcloud_data(self) -> Dict[str, Any]:
        """Generate word frequency data by country"""
        logger.info("Generating country-wise wordcloud data...")
        
        if 'country' not in self.articles_df.columns:
            logger.warning("No country column found")
            return {}
        
        country_data = {}
        
        # Group by country
        for country, country_df in self.articles_df.groupby('country'):
            if len(country_df) < 5:  # Skip countries with too few articles
                continue
                
            word_counter = Counter()
            
            for _, row in country_df.iterrows():
                if 'lemma_nostop' in row:
                    words = self._extract_words(row['lemma_nostop'])
                    word_counter.update(words)
            
            # Filter and get top words
            filtered_words = {word: count for word, count in word_counter.items() 
                             if count >= self.min_frequency}
            
            if filtered_words:
                top_words = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:100]
                wordcloud_data = [[word, count] for word, count in top_words]
                
                country_data[country] = {
                    "data": wordcloud_data,
                    "total_articles": len(country_df),
                    "total_words": sum(word_counter.values()),
                    "unique_words": len(word_counter)
                }
        
        logger.info(f"Generated wordcloud data for {len(country_data)} countries")
        return country_data
    
    def generate_temporal_wordcloud_data(self) -> Dict[str, Any]:
        """Generate word frequency data by year"""
        logger.info("Generating temporal wordcloud data...")
        
        if 'year' not in self.articles_df.columns:
            logger.warning("No year data available")
            return {}
        
        temporal_data = {}
        
        # Group by year
        for year, year_df in self.articles_df.groupby('year'):
            if pd.isna(year) or len(year_df) < 10:  # Skip years with too few articles
                continue
                
            word_counter = Counter()
            
            for _, row in year_df.iterrows():
                if 'lemma_nostop' in row:
                    words = self._extract_words(row['lemma_nostop'])
                    word_counter.update(words)
            
            # Filter and get top words
            filtered_words = {word: count for word, count in word_counter.items() 
                             if count >= self.min_frequency}
            
            if filtered_words:
                top_words = sorted(filtered_words.items(), key=lambda x: x[1], reverse=True)[:100]
                wordcloud_data = [[word, count] for word, count in top_words]
                
                temporal_data[str(int(year))] = {
                    "data": wordcloud_data,
                    "total_articles": len(year_df),
                    "total_words": sum(word_counter.values()),
                    "unique_words": len(word_counter)
                }
        
        logger.info(f"Generated wordcloud data for {len(temporal_data)} years")
        return temporal_data
    
    def save_wordcloud_data(self) -> None:
        """Generate and save all wordcloud data to JSON files"""
        logger.info("Generating and saving wordcloud data...")
        
        try:
            # Generate global wordcloud
            global_data = self.generate_global_wordcloud_data()
            global_path = self.output_dir / 'wordcloud-global.json'
            with open(global_path, 'w', encoding='utf-8') as f:
                json.dump(global_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved global wordcloud data to {global_path}")
            
            # Generate country wordclouds
            country_data = self.generate_country_wordcloud_data()
            country_path = self.output_dir / 'wordcloud-countries.json'
            with open(country_path, 'w', encoding='utf-8') as f:
                json.dump(country_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved country wordcloud data to {country_path}")
            
            # Generate temporal wordclouds
            temporal_data = self.generate_temporal_wordcloud_data()
            temporal_path = self.output_dir / 'wordcloud-temporal.json'
            with open(temporal_path, 'w', encoding='utf-8') as f:
                json.dump(temporal_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved temporal wordcloud data to {temporal_path}")
            
            # Save metadata
            metadata = {
                "generated_at": datetime.now().isoformat(),
                "total_articles": len(self.articles_df),
                "language_filter": "Français",
                "min_word_length": self.min_word_length,
                "min_frequency": self.min_frequency,
                "countries": list(country_data.keys()) if country_data else [],
                "years": sorted([int(year) for year in temporal_data.keys()]) if temporal_data else [],
                "exclude_words_count": len(self.exclude_words),
                "data_structure": {
                    "global": "Overall word frequencies across all French articles",
                    "countries": "Word frequencies grouped by country",
                    "temporal": "Word frequencies grouped by publication year"
                },
                "wordcloud_format": "Each data entry is [word, frequency] for wordcloud2.js"
            }
            
            metadata_path = self.output_dir / 'wordcloud-metadata.json'
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved metadata to {metadata_path}")
            
        except Exception as e:
            logger.error(f"Error generating wordcloud data: {e}")
            raise
    
    def process(self) -> None:
        """Main processing pipeline"""
        try:
            self.fetch_articles_data()
            self.save_wordcloud_data()
            logger.info("✅ Wordcloud data generation completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Wordcloud data generation failed: {e}")
            raise


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate wordcloud data from French IWAC articles')
    parser.add_argument('--output-dir', default='static/data', 
                       help='Output directory for JSON files (default: static/data)')
    parser.add_argument('--min-frequency', type=int, default=2,
                       help='Minimum word frequency threshold (default: 2)')
    parser.add_argument('--min-length', type=int, default=3,
                       help='Minimum word length (default: 3)')
    
    args = parser.parse_args()
    
    generator = IWACWordcloudGenerator(output_dir=args.output_dir)
    generator.min_frequency = args.min_frequency
    generator.min_word_length = args.min_length
    generator.process()


if __name__ == "__main__":
    main()