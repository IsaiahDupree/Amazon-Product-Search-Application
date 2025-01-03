import os
import requests
from typing import Dict, List, Optional
import json

class AmazonAPIClient:
    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY environment variable not set")
        
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'amazon-data-scraper124.p.rapidapi.com'
        }
        self.base_url = "https://amazon-data-scraper124.p.rapidapi.com"
    
    def search_products(self, query: str) -> Dict:
        """
        Search for products using the Amazon Data API
        """
        try:
            # Prepare API endpoint
            endpoint = f"{self.base_url}/search/{query}"
            
            # Make API request
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API request error: {str(e)}")
            return {"error": str(e)}
    
    def get_product_details(self, asin: str) -> Dict:
        """
        Get detailed information about a specific product
        """
        try:
            # Prepare API endpoint
            endpoint = f"{self.base_url}/product/{asin}"
            
            # Make API request
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API request error: {str(e)}")
            return {"error": str(e)}
    
    def format_search_results(self, api_response: Dict) -> List[Dict]:
        """Format the API response into a consistent structure"""
        try:
            if "error" in api_response:
                return []
            
            results = []
            products = api_response.get("results", [])
            
            for product in products:
                formatted = {
                    "name": product.get("name", ""),
                    "title": product.get("title", ""),
                    "url": product.get("url", ""),
                    "price": product.get("price", {}).get("current_price", "N/A"),
                    "rating": str(product.get("rating", "N/A")),
                    "brand": product.get("brand", ""),
                    "asin": product.get("asin", ""),
                    "image": product.get("thumbnail", "")
                }
                results.append(formatted)
            
            return results
            
        except Exception as e:
            print(f"Error formatting results: {str(e)}")
            return []
    
    def format_product_details(self, api_response: Dict) -> Dict:
        """Format the product details into a consistent structure"""
        try:
            if "error" in api_response:
                return api_response
            
            product = api_response.get("product", {})
            
            return {
                "name": product.get("name", ""),
                "title": product.get("title", ""),
                "description": product.get("description", ""),
                "features": product.get("feature_bullets", []),
                "specifications": product.get("specifications", {}),
                "price": product.get("price", {}).get("current_price", "N/A"),
                "rating": str(product.get("rating", "N/A")),
                "review_count": product.get("reviews_total", 0),
                "availability": product.get("availability", {}).get("status", "Unknown"),
                "images": product.get("images", []),
                "brand": product.get("brand", ""),
                "asin": product.get("asin", ""),
                "url": product.get("url", "")
            }
            
        except Exception as e:
            print(f"Error formatting product details: {str(e)}")
            return {"error": str(e)}
