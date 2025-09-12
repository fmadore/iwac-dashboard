#!/usr/bin/env python3
"""
IWAC Treemap Data Generator
Focused script to fetch data from Hugging Face and generate treemap data for countries visualization
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

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


class IWACTreemapGenerator:
    """Generate treemap data from IWAC dataset for countries visualization"""
    
    def __init__(self, output_dir: str = "../static/data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Mapping from subset names to document types
        self.subset_to_type = {
            'articles': 'Article de presse',
            'documents': 'Document',
            'audiovisual': 'Audiovisuel', 
            'publications': 'Publication islamique'
        }
        
        # Subsets that have newspaper column (3rd level)
        self.subsets_with_newspaper = {'articles', 'publications'}
        
        # Store combined data
        self.combined_df = None
        
    def fetch_dataset(self) -> None:
        """Fetch all subsets from the IWAC dataset (except index)"""
        logger.info("Fetching IWAC dataset from Hugging Face...")
        
        dataset_name = "fmadore/islam-west-africa-collection"
        all_data = []
        
        for subset_name, doc_type in self.subset_to_type.items():
            try:
                logger.info(f"Loading subset: {subset_name}")
                dataset = load_dataset(dataset_name, subset_name)
                
                # Convert to pandas DataFrame
                df = dataset['train'].to_pandas()
                
                # Add document type and subset info
                df['type'] = doc_type
                df['subset'] = subset_name
                
                # Store raw data
                all_data.append(df)
                
                logger.info(f"Loaded {len(df)} records from {subset_name}")
                
            except Exception as e:
                logger.error(f"Error loading subset {subset_name}: {e}")
                continue
        
        if all_data:
            # Combine all dataframes
            self.combined_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"Total records loaded: {len(self.combined_df)}")
        else:
            raise Exception("No data was successfully loaded")
    
    def generate_treemap_data(self) -> Dict[str, Any]:
        """Generate hierarchical data structure for the countries treemap"""
        logger.info("Generating treemap data...")
        
        # Filter out records without country
        df_with_country = self.combined_df.dropna(subset=['country'])
        logger.info(f"Records with country data: {len(df_with_country)}")
        
        # Create hierarchical structure
        treemap_data = {
            "name": "Countries",
            "value": 0,  # Will be calculated by LayerChart
            "children": []
        }
        
        # Group by country (Level 1)
        country_groups = df_with_country.groupby('country')
        
        for country_name, country_data in country_groups:
            country_node = {
                "name": country_name,
                "value": len(country_data),
                "children": []
            }
            
            # Group by document type within each country (Level 2)
            type_groups = country_data.groupby('type')
            
            for doc_type, type_data in type_groups:
                type_node = {
                    "name": doc_type,
                    "value": len(type_data),
                    "children": []
                }
                
                # Level 3: newspaper (only for articles and publications subsets)
                subset_name = type_data['subset'].iloc[0]  # All rows should have same subset
                
                if subset_name in self.subsets_with_newspaper:
                    # Check if newspaper column exists and has data
                    if 'newspaper' in type_data.columns:
                        newspaper_data = type_data.dropna(subset=['newspaper'])
                        
                        if len(newspaper_data) > 0:
                            newspaper_groups = newspaper_data.groupby('newspaper')
                            
                            for newspaper_name, news_data in newspaper_groups:
                                newspaper_node = {
                                    "name": newspaper_name,
                                    "value": len(news_data)
                                }
                                type_node["children"].append(newspaper_node)
                            
                            # Sort newspapers by value (descending)
                            type_node["children"].sort(key=lambda x: x["value"], reverse=True)
                        else:
                            logger.info(f"No newspaper data found for {doc_type} in {country_name}")
                    else:
                        logger.info(f"No newspaper column found for {doc_type}")
                else:
                    # audiovisual and document don't have newspaper level
                    logger.info(f"Subset {subset_name} ({doc_type}) doesn't have newspaper children")
                
                country_node["children"].append(type_node)
            
            # Sort document types by value (descending)
            country_node["children"].sort(key=lambda x: x["value"], reverse=True)
            treemap_data["children"].append(country_node)
        
        # Sort countries by value (descending)
        treemap_data["children"].sort(key=lambda x: x["value"], reverse=True)
        
        # Log some statistics
        total_countries = len(treemap_data["children"])
        total_documents = sum(country["value"] for country in treemap_data["children"])
        
        logger.info(f"Generated treemap with {total_countries} countries and {total_documents} documents")
        
        return treemap_data
    
    def save_treemap_data(self) -> None:
        """Generate and save treemap data to JSON file"""
        logger.info("Generating and saving treemap data...")
        
        try:
            treemap_data = self.generate_treemap_data()
            
            # Save treemap data
            treemap_path = self.output_dir / 'treemap-countries.json'
            with open(treemap_path, 'w', encoding='utf-8') as f:
                json.dump(treemap_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved treemap data to {treemap_path}")
            
            # Save metadata
            metadata = {
                "generated_at": datetime.now().isoformat(),
                "total_records": len(self.combined_df),
                "records_with_country": len(self.combined_df.dropna(subset=['country'])),
                "subsets_processed": list(self.subset_to_type.keys()),
                "countries": sorted(self.combined_df['country'].dropna().unique().tolist()),
                "document_types": sorted(self.combined_df['type'].unique().tolist()),
                "subsets_with_newspaper": list(self.subsets_with_newspaper),
                "structure": {
                    "level_1": "Countries (from country column)",
                    "level_2": "Document types (mapped from subset names)",
                    "level_3": "Newspapers (only for articles and publications subsets)"
                }
            }
            
            metadata_path = self.output_dir / 'treemap-metadata.json'
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved metadata to {metadata_path}")
            
        except Exception as e:
            logger.error(f"Error generating treemap data: {e}")
            raise
    
    def process(self) -> None:
        """Main processing pipeline"""
        try:
            self.fetch_dataset()
            self.save_treemap_data()
            logger.info("✅ Treemap data generation completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Treemap data generation failed: {e}")
            raise


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate treemap data from IWAC dataset')
    parser.add_argument('--output-dir', default='../static/data', 
                       help='Output directory for JSON files (default: ../static/data)')
    
    args = parser.parse_args()
    
    generator = IWACTreemapGenerator(output_dir=args.output_dir)
    generator.process()


if __name__ == "__main__":
    main()