import os
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup
import json

class GoogleSearchClient:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.search_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")
        if not self.search_engine_id:
            raise ValueError("GOOGLE_SEARCH_ENGINE_ID environment variable not set")
    
    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Search Google for product information
        """
        try:
            # Add product-related terms to the query
            enhanced_query = f"{query} product amazon"
            
            # Prepare the URL
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': enhanced_query,
                'num': num_results
            }
            
            # Make the request
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Parse results
            results = []
            data = response.json()
            
            if 'items' in data:
                for item in data['items']:
                    result = {
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'source': 'google'
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            print(f"Google search error: {str(e)}")
            return []
    
    def extract_product_info(self, results: List[Dict]) -> Dict:
        """
        Extract product information from search results
        """
        try:
            # Initialize product info
            product_info = {
                'likely_products': [],
                'suggested_terms': [],
                'confidence': 0.0
            }
            
            # Analyze results
            for result in results:
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                
                # Look for product indicators
                product_indicators = ['amazon', 'buy', 'price', 'review', 'product']
                confidence = sum(1 for ind in product_indicators if ind in title or ind in snippet) / len(product_indicators)
                
                # Extract potential product names
                if confidence > 0.3:  # Threshold for considering it a product
                    # Clean up the title
                    product_name = title.split('-')[0].strip()
                    if 'amazon' in product_name.lower():
                        product_name = product_name.lower().replace('amazon', '').strip()
                    
                    if product_name and product_name not in product_info['likely_products']:
                        product_info['likely_products'].append(product_name)
                
                # Extract suggested search terms
                if snippet:
                    # Look for related terms in snippet
                    terms = snippet.split()
                    relevant_terms = [term for term in terms 
                                   if len(term) > 3 and 
                                   term.isalnum() and 
                                   term not in ['amazon', 'buy', 'price', 'review']]
                    product_info['suggested_terms'].extend(relevant_terms[:3])
            
            # Calculate overall confidence
            product_info['confidence'] = len(product_info['likely_products']) / len(results) if results else 0.0
            
            # Remove duplicates from suggested terms
            product_info['suggested_terms'] = list(set(product_info['suggested_terms']))
            
            return product_info
            
        except Exception as e:
            print(f"Error extracting product info: {str(e)}")
            return {
                'likely_products': [],
                'suggested_terms': [],
                'confidence': 0.0
            }
    
    def enhance_product_query(self, query: str) -> Dict:
        """
        Use Google search to enhance a product query
        """
        try:
            # First search Google
            results = self.search(query)
            
            if not results:
                return {
                    'enhanced_query': query,
                    'confidence': 0.0,
                    'suggestions': []
                }
            
            # Extract product information
            product_info = self.extract_product_info(results)
            
            # Create enhanced query
            enhanced_query = query
            if product_info['likely_products']:
                # Use the most relevant product name
                enhanced_query = product_info['likely_products'][0]
            
            # Add relevant terms if confidence is low
            if product_info['confidence'] < 0.5 and product_info['suggested_terms']:
                enhanced_query = f"{enhanced_query} {' '.join(product_info['suggested_terms'][:2])}"
            
            return {
                'enhanced_query': enhanced_query,
                'confidence': product_info['confidence'],
                'suggestions': product_info['likely_products'][1:] if len(product_info['likely_products']) > 1 else []
            }
            
        except Exception as e:
            print(f"Error enhancing query: {str(e)}")
            return {
                'enhanced_query': query,
                'confidence': 0.0,
                'suggestions': []
            }
