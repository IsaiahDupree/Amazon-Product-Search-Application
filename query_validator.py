import openai
import os
from typing import Dict, Optional
from google_search_client import GoogleSearchClient

class QueryValidator:
    def __init__(self):
        self.client = openai.Client(api_key=os.getenv('OPENAI_API_KEY'))
        self.google_client = GoogleSearchClient()
    
    def validate_query(self, query: str) -> Dict:
        """
        Validate if a query is a product search or something else.
        Returns a dict with validation result and suggested action.
        """
        try:
            # First try to enhance query with Google Search
            google_results = self.google_client.enhance_product_query(query)
            
            # If Google found product information with high confidence
            if google_results['confidence'] > 0.5:
                return {
                    'is_product_search': True,
                    'category': 'product',
                    'enhanced_query': google_results['enhanced_query'],
                    'suggestion': f"Found product: {google_results['enhanced_query']}",
                    'explanation': "Query enhanced using Google Search results",
                    'alternative_suggestions': google_results['suggestions']
                }
            
            # If Google results weren't confident, use OpenAI
            system_message = """You are a query classifier that determines if a user's query is a product search 
            or another type of request (like a recipe, medical advice, etc.). For product searches, suggest 
            improvements to make the search more effective.
            
            Return a JSON object with:
            1. is_product_search: boolean
            2. category: string (e.g., "product", "recipe", "medical", "other")
            3. suggestion: string (if product search, how to improve it; if not, what the user might be looking for)
            4. enhanced_query: string (if product search, a better search query)
            5. explanation: string (why this classification was made)"""
            
            # Get completion from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Classify this query: {query}"}
                ],
                temperature=0.7,
                max_tokens=300,
                response_format={ "type": "json_object" }
            )
            
            # Parse the response
            result = eval(response.choices[0].message.content)
            
            # If it's a product search, try to enhance with Google results
            if result['is_product_search'] and google_results['enhanced_query'] != query:
                result['enhanced_query'] = google_results['enhanced_query']
                result['alternative_suggestions'] = google_results['suggestions']
            
            return result
            
        except Exception as e:
            print(f"Error validating query: {str(e)}")
            # On error, try to use Google results directly
            if google_results['enhanced_query'] != query:
                return {
                    'is_product_search': True,
                    'category': 'product',
                    'enhanced_query': google_results['enhanced_query'],
                    'suggestion': "Using Google Search results",
                    'explanation': f"Validation error, using Google results: {str(e)}",
                    'alternative_suggestions': google_results['suggestions']
                }
            
            return {
                'is_product_search': True,
                'category': 'product',
                'suggestion': "Could not validate query",
                'enhanced_query': query,
                'explanation': f"Validation error: {str(e)}"
            }
    
    def handle_non_product_query(self, query: str, category: str) -> Dict:
        """Handle queries that are not product searches"""
        try:
            # Create system message based on category
            system_messages = {
                'recipe': """You are a helpful cooking assistant. Provide a brief recipe suggestion 
                or cooking tip based on the query.""",
                'medical': """You are a helpful assistant. Remind the user to consult healthcare 
                professionals for medical advice, but you can provide general health information.""",
                'other': """You are a helpful assistant. Provide a brief, helpful response to the 
                user's query."""
            }
            
            # Try Google search first for more context
            google_results = self.google_client.search(query)
            context = ""
            if google_results:
                # Extract relevant information from search results
                snippets = [result['snippet'] for result in google_results[:2]]
                context = f"\nContext from search results:\n" + "\n".join(snippets)
            
            system_message = system_messages.get(category, system_messages['other'])
            if context:
                system_message += context
            
            # Get completion from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": query}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return {
                'response': response.choices[0].message.content,
                'category': category,
                'search_results': google_results[:3] if google_results else []
            }
            
        except Exception as e:
            print(f"Error handling non-product query: {str(e)}")
            return {
                'response': f"I apologize, but I couldn't process that query. Error: {str(e)}",
                'category': category
            }
