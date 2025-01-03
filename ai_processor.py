import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AIProcessor:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-3.5-turbo"
        self.history_file = "search_history.json"
    
    def process_user_input(self, raw_input: str) -> Dict:
        """
        Process user input using AI to structure and enhance the search query
        
        Args:
            raw_input (str): Raw user input text
            
        Returns:
            Dict: Processed input with structured data
        """
        try:
            # First, split the input into lines and clean it
            input_lines = [line.strip() for line in raw_input.split('\n') if line.strip()]
            
            # Prepare the prompt for the AI
            prompt = f"""
            Process this list of products and return a JSON array of product objects.
            Each product should be in this exact format, no other format is acceptable:
            {{
                "product_name": "exact product name",
                "search_keywords": ["keyword1", "keyword2"]
            }}

            Input products:
            {raw_input}

            Respond ONLY with the JSON array, no other text. Example:
            [
                {{
                    "product_name": "Example Product",
                    "search_keywords": ["example", "product"]
                }}
            ]
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a JSON formatter that converts product lists into structured data. Only output valid JSON arrays."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            # Extract and parse the AI response
            ai_response = response.choices[0].message.content
            
            try:
                # Try to parse the JSON response
                processed_data = json.loads(ai_response)
                
                # If we got a dict instead of a list, wrap it in a list
                if isinstance(processed_data, dict):
                    if "products" in processed_data:
                        processed_data = processed_data["products"]
                    else:
                        processed_data = [processed_data]
                
                # Ensure we have a list of products
                if not isinstance(processed_data, list):
                    raise ValueError("AI response is not a list of products")
                
                return {
                    "products": processed_data,
                    "total_products": len(processed_data)
                }
                
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract product names directly
                products = []
                for line in input_lines:
                    if line:
                        products.append({
                            "product_name": line,
                            "search_keywords": line.split()
                        })
                
                return {
                    "products": products,
                    "total_products": len(products)
                }
            
        except Exception as e:
            # Fallback: just use the raw input lines as product names
            try:
                products = []
                for line in input_lines:
                    if line:
                        products.append({
                            "product_name": line,
                            "search_keywords": line.split()
                        })
                
                return {
                    "products": products,
                    "total_products": len(products),
                    "warning": f"Used fallback processing due to error: {str(e)}"
                }
            except Exception as fallback_error:
                return {
                    "error": f"Failed to process input: {str(fallback_error)}",
                    "raw_input": raw_input
                }
    
    def save_search_history(self, search_data: Dict):
        """Save search data to history file"""
        try:
            # Load existing history
            history = self.load_search_history()
            
            # Add timestamp to new search
            search_data["timestamp"] = datetime.now().isoformat()
            
            # Add new search to history
            history.append(search_data)
            
            # Save updated history
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save search history: {str(e)}")
    
    def load_search_history(self) -> List[Dict]:
        """Load search history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Failed to load search history: {str(e)}")
            return []
    
    def get_search_suggestions(self, current_input: str) -> List[str]:
        """Get AI suggestions for the current search input"""
        try:
            prompt = f"""
            Based on this partial product search:
            {current_input}
            
            Suggest 3 specific improvements or additions that could help get better search results.
            Format each suggestion on a new line with a '-' prefix.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides specific suggestions to improve product searches."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            suggestions = response.choices[0].message.content.strip().split('\n')
            return [s.strip('- ') for s in suggestions if s.strip()]
            
        except Exception as e:
            return [f"Error getting suggestions: {str(e)}"]
    
    def analyze_products(self, products: List[Dict], requirements: str = None, 
                        min_budget: float = None, max_budget: float = None,
                        include_market_research: bool = True) -> Dict:
        """
        Analyze and compare products, suggesting the best options based on requirements and budget range
        
        Args:
            products: List of product dictionaries with details
            requirements: Optional string describing specific needs/requirements
            min_budget: Optional minimum budget
            max_budget: Optional maximum budget
            include_market_research: Whether to include market research and alternatives
            
        Returns:
            Dict with analysis results
        """
        try:
            # Prepare product data for analysis
            product_details = []
            for p in products:
                details = {
                    "name": p.get("product_name", "Unknown"),
                    "price": p.get("price", "Unknown"),
                    "rating": p.get("rating", "Unknown"),
                    "features": p.get("features", []),
                    "specs": p.get("specifications", {}),
                    "url": p.get("url", "")
                }
                product_details.append(details)
            
            # Prepare the analysis prompt
            prompt = f"""
            Analyze these products and provide a detailed comparison and recommendations.
            
            Products:
            {json.dumps(product_details, indent=2)}
            
            User Requirements:
            {requirements if requirements else "Not specified"}
            
            Budget Range:
            Minimum: {"$" + str(min_budget) if min_budget else "Not specified"}
            Maximum: {"$" + str(max_budget) if max_budget else "Not specified"}
            
            Include Market Research: {"Yes" if include_market_research else "No"}
            
            Provide analysis in this JSON format:
            {{
                "market_overview": "Overview of the current market situation and trends for these types of products",
                "best_overall": {{
                    "product_name": "name",
                    "reasoning": "detailed explanation"
                }},
                "best_value": {{
                    "product_name": "name",
                    "reasoning": "detailed explanation"
                }},
                "premium_pick": {{
                    "product_name": "name",
                    "reasoning": "detailed explanation"
                }},
                "comparisons": [
                    {{
                        "aspect": "aspect name",
                        "analysis": "detailed comparison",
                        "alternatives": [
                            "suggestion for alternative product or solution",
                            "another alternative"
                        ]
                    }}
                ],
                "tradeoffs": [
                    {{
                        "description": "tradeoff description",
                        "affected_products": ["product names"],
                        "recommendation": "how to handle this tradeoff",
                        "alternatives": [
                            "alternative solution 1",
                            "alternative solution 2"
                        ]
                    }}
                ],
                "market_insights": [
                    {{
                        "trend": "market trend description",
                        "impact": "how it affects the decision",
                        "recommendation": "what to do about it"
                    }}
                ]
            }}
            
            Focus on:
            1. Detailed feature comparisons
            2. Price-performance analysis
            3. Long-term value considerations
            4. Compatibility and integration
            5. Future upgrade potential
            6. Alternative options and solutions
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a product analysis expert who provides detailed comparisons and recommendations, including market research and alternatives when requested."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            analysis = json.loads(response.choices[0].message.content)
            
            # If market research wasn't requested, remove those sections
            if not include_market_research:
                analysis.pop("market_overview", None)
                analysis.pop("market_insights", None)
                for comp in analysis.get("comparisons", []):
                    comp.pop("alternatives", None)
                for tradeoff in analysis.get("tradeoffs", []):
                    tradeoff.pop("alternatives", None)
            
            return analysis
            
        except Exception as e:
            return {
                "error": f"Failed to analyze products: {str(e)}",
                "products_analyzed": len(products)
            }
    
    def suggest_configuration(self, selected_products: List[Dict], 
                            min_budget: float = None, max_budget: float = None) -> Dict:
        """
        Suggest optimal configuration based on selected products and budget range
        
        Args:
            selected_products: List of selected product dictionaries
            min_budget: Optional minimum budget
            max_budget: Optional maximum budget
            
        Returns:
            Dict with configuration suggestions
        """
        try:
            prompt = f"""
            Suggest optimal configuration based on these products:
            {json.dumps(selected_products, indent=2)}
            
            Budget Range:
            Minimum: {"$" + str(min_budget) if min_budget else "Not specified"}
            Maximum: {"$" + str(max_budget) if max_budget else "Not specified"}
            
            Provide suggestions in this JSON format:
            {{
                "configurations": [
                    {{
                        "name": "configuration name",
                        "products": ["product names"],
                        "total_cost": "estimated total",
                        "performance_level": "description",
                        "pros": ["list of pros"],
                        "cons": ["list of cons"]
                    }}
                ],
                "budget_analysis": {{
                    "within_budget": true/false,
                    "total_cost": "amount",
                    "savings_suggestions": ["suggestions"]
                }},
                "compatibility_notes": ["important compatibility information"],
                "upgrade_path": ["suggested future upgrades"],
                "alternative_configurations": [
                    {{
                        "scenario": "use case or budget scenario",
                        "suggested_changes": ["changes to make"],
                        "impact": "impact on performance/cost"
                    }}
                ]
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a system configuration expert who provides detailed build suggestions and compatibility analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            suggestions = json.loads(response.choices[0].message.content)
            return suggestions
            
        except Exception as e:
            return {
                "error": f"Failed to generate configuration suggestions: {str(e)}",
                "products_considered": len(selected_products)
            }

    def find_alternatives(self, product: Dict, min_budget: float = None, max_budget: float = None) -> List[Dict]:
        """
        Find alternative products similar to the given product
        
        Args:
            product: Product to find alternatives for
            min_budget: Optional minimum budget
            max_budget: Optional maximum budget
            
        Returns:
            List of alternative products
        """
        try:
            prompt = f"""
            Find alternative products similar to this product:
            {json.dumps(product, indent=2)}
            
            Budget Range:
            Minimum: {"$" + str(min_budget) if min_budget else "Not specified"}
            Maximum: {"$" + str(max_budget) if max_budget else "Not specified"}
            
            Provide alternatives in this JSON format:
            [
                {{
                    "name": "Product name",
                    "price": "Price in USD",
                    "rating": "Rating out of 5",
                    "specs": "Key specifications",
                    "reviews": "Summary of reviews",
                    "url": "Product URL",
                    "comparison": {{
                        "pros": ["advantages compared to original"],
                        "cons": ["disadvantages compared to original"],
                        "price_diff": "Price difference from original",
                        "performance_diff": "Performance difference"
                    }}
                }}
            ]
            
            Focus on:
            1. Similar price range (within budget constraints)
            2. Comparable or better specifications
            3. Good user ratings and reviews
            4. Available from reputable sellers
            5. Recent models/releases
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a product comparison expert who helps find and evaluate alternative products."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            alternatives = json.loads(response.choices[0].message.content)
            return alternatives
            
        except Exception as e:
            raise Exception(f"Failed to find alternatives: {str(e)}")

    def enhance_search_query(self, query: str) -> Dict:
        """Enhance a vague product search query with more specific details"""
        try:
            # Create a system message for the AI
            system_message = """You are a computer hardware expert assistant. Your task is to enhance vague product search queries 
            with specific, relevant details for PC components. Focus on key specifications and requirements that would help find 
            the right product. Return a JSON object with:
            1. enhanced_query: A more detailed search query
            2. category: The product category (GPU, CPU, RAM, etc.)
            3. suggested_filters: Key specifications to consider
            4. explanation: Why these enhancements help"""
            
            # Create the user message with the query
            user_message = f"Please enhance this PC component search query: {query}"
            
            # Get completion from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=300,
                response_format={ "type": "json_object" }
            )
            
            # Parse the response
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error enhancing query: {str(e)}")
            # Return original query if enhancement fails
            return {
                "enhanced_query": query,
                "category": "Unknown",
                "suggested_filters": [],
                "explanation": f"Could not enhance query: {str(e)}"
            }

    def suggest_alternatives(self, product_info: Dict) -> List[Dict]:
        """Suggest alternative products based on given product information"""
        try:
            # Create system message for alternatives
            system_message = """You are a computer hardware expert. Given a PC component's details, suggest alternative products 
            with similar or better specifications. Consider price-performance ratio, compatibility, and user needs. Return a JSON 
            array of alternative products with name, estimated price, key features, and reasoning."""
            
            # Create user message with product info
            user_message = f"Please suggest alternatives for this product: {json.dumps(product_info)}"
            
            # Get completion from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={ "type": "json_object" }
            )
            
            # Parse and return alternatives
            result = json.loads(response.choices[0].message.content)
            return result.get("alternatives", [])
            
        except Exception as e:
            print(f"Error suggesting alternatives: {str(e)}")
            return []
