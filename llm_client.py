import os
from typing import List, Dict
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        openai.api_key = self.api_key
        self.model = "gpt-3.5-turbo"  # Can be updated to gpt-4 if needed

    def summarize_product(self, product_info: Dict) -> str:
        """
        Generate a concise summary of a product
        
        Args:
            product_info (Dict): Product information including features, specs, etc.
            
        Returns:
            str: AI-generated summary of the product
        """
        # Create a clean text representation of the product info
        product_text = (
            f"Product: {product_info.get('title')}\n"
            f"Brand: {product_info.get('brand')}\n"
            f"Price: {product_info.get('price')}\n"
            f"Rating: {product_info.get('rating')}\n"
            "Features:\n" + "\n".join([f"- {f}" for f in product_info.get('features', [])])
        )

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful product analyst. Summarize the following product information concisely, highlighting key features and potential pros/cons."},
                    {"role": "user", "content": product_text}
                ],
                max_tokens=200,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            return "Unable to generate summary"

    def generate_comparison_table(self, products: List[Dict]) -> str:
        """
        Generate a markdown comparison table for multiple products
        
        Args:
            products (List[Dict]): List of product information dictionaries
            
        Returns:
            str: Markdown-formatted comparison table
        """
        # Create a text representation of all products
        products_text = "\n".join([
            f"Product {i+1}:\n"
            f"Title: {p.get('title')}\n"
            f"Brand: {p.get('brand')}\n"
            f"Price: {p.get('price')}\n"
            f"Rating: {p.get('rating')}\n"
            f"Features: {', '.join(p.get('features', []))}\n"
            for i, p in enumerate(products)
        ])

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful product comparison expert. Create a markdown comparison table for the following products. Include columns for Title, Brand, Price, Rating, and Key Features. Keep it concise and highlight the most important differences."},
                    {"role": "user", "content": products_text}
                ],
                max_tokens=500,
                temperature=0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating comparison table: {e}")
            return "Unable to generate comparison table"
