import requests
import time
import json
from typing import List, Dict, Optional, Tuple, Union
import re
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse
from amazon_api_client import AmazonAPIClient

class BatchSearcher:
    def __init__(self):
        self.api_client = AmazonAPIClient()
        self._stop = False
    
    def search(self, query: str) -> List[Dict]:
        """Search for products with the given query"""
        try:
            # Make API request
            response = self.api_client.search_products(query)
            
            if "error" in response:
                print(f"API error: {response['error']}")
                return []
            
            # Format results
            results = self.api_client.format_search_results(response)
            
            # Add additional product details if needed
            if results and len(results) > 0:
                for result in results:
                    if self._stop:
                        break
                    
                    # Get ASIN
                    asin = result.get("asin")
                    if asin:
                        # Get additional details
                        details = self.api_client.get_product_details(asin)
                        if "error" not in details:
                            # Update result with additional details
                            formatted_details = self.api_client.format_product_details(details)
                            result.update(formatted_details)
                    
                    # Add small delay to avoid rate limiting
                    time.sleep(0.1)
            
            return results
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            return []
    
    def stop(self):
        """Stop the search operation"""
        self._stop = True
    
    def get_product_details(self, url: str) -> Dict:
        """Get detailed information about a product from its URL"""
        try:
            # Extract ASIN from URL
            asin = self._extract_asin_from_url(url)
            if not asin:
                return {"error": "Could not extract ASIN from URL"}
            
            # Get product details from API
            details = self.api_client.get_product_details(asin)
            
            if "error" in details:
                return details
            
            # Format the details
            formatted_details = {
                "description": details.get("data", {}).get("description", ""),
                "specifications": details.get("data", {}).get("specifications", {}),
                "features": details.get("data", {}).get("feature_bullets", [])
            }
            
            return formatted_details
            
        except Exception as e:
            print(f"Error getting product details: {str(e)}")
            return {
                "error": str(e),
                "status": "error"
            }
    
    def _extract_asin_from_url(self, url: str) -> Optional[str]:
        """Extract ASIN from Amazon URL"""
        try:
            # Try to find ASIN in the URL path
            path = urlparse(url).path
            match = re.search(r'/dp/([A-Z0-9]{10})', path)
            if match:
                return match.group(1)
            
            # Try to find ASIN in query parameters
            query = urlparse(url).query
            if 'asin=' in query.lower():
                asin = re.search(r'asin=([A-Z0-9]{10})', query, re.I)
                if asin:
                    return asin.group(1)
            
            return None
            
        except Exception:
            return None

class BatchProductSearcher:
    def __init__(self):
        self.batch_searcher = BatchSearcher()
    
    def parse_product_list(self, text: str) -> List[Tuple[str, str]]:
        """Parse a text containing product names and geni.us links."""
        # Split text into lines and remove empty lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        products = []
        
        for line in lines:
            # Try to extract product name and link
            match = re.match(r'(.*?)\s+(https://geni\.us/\S+)', line)
            if match:
                name, link = match.groups()
                products.append((name.strip(), link.strip()))
        
        return products
    
    def get_product_info(self, product_name: str) -> Dict:
        """Search for a product and get its details."""
        try:
            # Search for the product
            results = self.batch_searcher.search(product_name)
            if not results:
                return {
                    "name": product_name,
                    "status": "not_found",
                    "error": "No products found"
                }
            
            # Get the first product's details
            first_product = results[0]
            url = first_product.get("url")
            
            if not url:
                return {
                    "name": product_name,
                    "status": "no_url",
                    "error": "No URL found"
                }
            
            # Get detailed information
            details = self.batch_searcher.get_product_details(url)
            if "error" in details:
                return {
                    "name": product_name,
                    "status": "error",
                    "error": details["error"]
                }
            
            # Extract product information
            product_info = {
                "name": product_name,
                "title": first_product.get("title"),
                "price": first_product.get("price"),
                "rating": first_product.get("rating"),
                "review_count": first_product.get("review_count"),
                "description": details.get("description"),
                "specifications": details.get("specifications"),
                "features": details.get("features"),
                "status": "found"
            }
            
            return product_info
            
        except Exception as e:
            return {
                "name": product_name,
                "status": "error",
                "error": str(e)
            }
    
    def process_product_list(self, product_list_text: str) -> pd.DataFrame:
        """Process a list of products and return results as a DataFrame."""
        # Parse the product list
        products = self.parse_product_list(product_list_text)
        results = []
        
        print(f"\nProcessing {len(products)} products...")
        
        for name, link in products:
            print(f"\nSearching for: {name}")
            # Get product information
            info = self.get_product_info(name)
            info["original_link"] = link
            results.append(info)
            # Add a small delay to avoid rate limits
            time.sleep(1)
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Reorder columns for better readability
        columns = ["name", "title", "price", "rating", "review_count", "description", "specifications", "features", "original_link", "status"]
        all_columns = columns + [col for col in df.columns if col not in columns]
        df = df[all_columns]
        
        return df
    
    def save_results(self, df: pd.DataFrame, output_file: str = "product_results.csv"):
        """Save results to CSV and generate a summary."""
        # Save to CSV
        df.to_csv(output_file, index=False)
        print(f"\nResults saved to {output_file}")
        
        # Generate summary
        summary = {
            "total_products": len(df),
            "found_products": len(df[df["status"] == "found"]),
            "not_found": len(df[df["status"] != "found"]),
            "average_price": df["price"].mean() if "price" in df else None,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save summary
        with open("search_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        return summary

def main():
    searcher = BatchProductSearcher()
    
    print("=== Batch Product Search Tool ===")
    print("Paste your product list below (press Ctrl+Z or Ctrl+D and Enter when done):")
    
    try:
        product_list = ""
        while True:
            try:
                line = input()
                product_list += line + "\n"
            except EOFError:
                break
    except KeyboardInterrupt:
        print("\nInput cancelled.")
        return
    
    if not product_list.strip():
        print("No input provided.")
        return
    
    print("\nProcessing your product list...")
    df = searcher.process_product_list(product_list)
    
    # Save results
    summary = searcher.save_results(df)
    
    # Print summary
    print("\nSearch Summary:")
    print(f"Total products processed: {summary['total_products']}")
    print(f"Products found: {summary['found_products']}")
    print(f"Products not found: {summary['not_found']}")
    if summary['average_price']:
        print(f"Average price: ${summary['average_price']:.2f}")
    
    print("\nResults have been saved to 'product_results.csv'")
    print("Summary has been saved to 'search_summary.json'")

if __name__ == "__main__":
    main()
