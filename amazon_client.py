import os
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AmazonClient:
    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY")
        if not self.api_key:
            raise ValueError("RAPIDAPI_KEY not found in environment variables")
        
        self.base_url = "https://real-time-amazon-data.p.rapidapi.com"
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
        }

    def search_products(self, query: str, page: int = 1, country: str = "US") -> Dict:
        """
        Search for products on Amazon
        
        Args:
            query (str): Search term
            page (int): Page number for pagination
            country (str): Country code (e.g., "US", "UK")
            
        Returns:
            Dict: JSON response containing search results
        """
        url = f"{self.base_url}/search"
        params = {
            "query": query,
            "page": page,
            "country": country
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error searching products: {e}")
            return {"error": str(e)}

    def get_product_details(self, asin: str, country: str = "US") -> Dict:
        """
        Get detailed information about a specific product
        
        Args:
            asin (str): Amazon Standard Identification Number
            country (str): Country code (e.g., "US", "UK")
            
        Returns:
            Dict: JSON response containing product details
        """
        url = f"{self.base_url}/product-details"
        params = {
            "asin": asin,
            "country": country
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting product details: {e}")
            return {"error": str(e)}

    def extract_product_info(self, product_data: Dict) -> Dict:
        """
        Extract relevant information from product data
        
        Args:
            product_data (Dict): Raw product data from API
            
        Returns:
            Dict: Cleaned product information
        """
        data = product_data.get("data", {})
        return {
            "title": data.get("product_title"),
            "asin": data.get("asin"),
            "price": data.get("product_price"),
            "rating": data.get("product_star_rating"),
            "url": data.get("product_url"),
            "image": data.get("product_image"),
            "brand": data.get("product_brand"),
            "features": data.get("product_features", [])
        }
