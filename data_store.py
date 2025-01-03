import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import uuid

class SearchHistoryStore:
    def __init__(self, data_dir: str = "data"):
        """Initialize the search history store
        
        Args:
            data_dir: Directory to store the search data
        """
        self.data_dir = data_dir
        self.search_file = os.path.join(data_dir, "search_history.json")
        self.alternatives_file = os.path.join(data_dir, "alternatives_history.json")
        self.results_dir = os.path.join(data_dir, "search_results")
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)
    
    def save_search(self, query: str, results: List[Dict], metadata: Optional[Dict] = None) -> str:
        """Save a search and its results
        
        Args:
            query: The search query
            results: List of dictionaries containing search results
            metadata: Optional metadata about the search
            
        Returns:
            str: Search ID
        """
        try:
            # Generate search ID based on timestamp
            search_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Prepare search record
            search_record = {
                "id": search_id,
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "result_count": len(results),
                "metadata": metadata or {}
            }
            
            # Save results to JSON
            results_file = os.path.join(self.results_dir, f"{search_id}.json")
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Store relative path in search record
            search_record["results_file"] = os.path.relpath(results_file, start=self.data_dir)
            
            # Update search history
            history = self.load_search_history()
            history.append(search_record)
            
            # Save updated history
            with open(self.search_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            return search_id
            
        except Exception as e:
            print(f"Failed to save search: {str(e)}")
            raise
    
    def load_search_history(self) -> List[Dict]:
        """Load all search history records
        
        Returns:
            List of search history records
        """
        try:
            if os.path.exists(self.search_file):
                with open(self.search_file, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Failed to load search history: {str(e)}")
            return []
    
    def load_search_results(self, search_id: str) -> Optional[List[Dict]]:
        """Load results for a specific search
        
        Args:
            search_id: ID of the search to load
            
        Returns:
            List of dictionaries containing the search results, or None if not found
        """
        try:
            # Find search record
            history = self.load_search_history()
            search_record = next((r for r in history if r["id"] == search_id), None)
            
            if not search_record:
                print(f"Search record not found for ID: {search_id}")
                return None
            
            if "results_file" not in search_record:
                print(f"Results file not specified in search record: {search_id}")
                return None
            
            # Convert relative path to absolute path
            results_file = os.path.join(self.data_dir, search_record["results_file"])
            if not os.path.exists(results_file):
                print(f"Results file not found: {results_file}")
                return None
            
            # Try loading as JSON first
            if results_file.endswith('.json'):
                try:
                    with open(results_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Ensure data is a list
                        if isinstance(data, dict):
                            data = [data]
                        return data
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {str(e)}")
                except Exception as e:
                    print(f"Error reading JSON file: {str(e)}")
            
            # Fall back to CSV if JSON fails or file is CSV
            if results_file.endswith('.csv'):
                try:
                    df = pd.read_csv(results_file)
                    # Convert DataFrame to list of dictionaries
                    data = df.to_dict('records')
                    return data
                except Exception as e:
                    print(f"Error reading CSV file: {str(e)}")
            
            print(f"Unsupported file format or corrupted file: {results_file}")
            return None
            
        except Exception as e:
            print(f"Failed to load search results: {str(e)}")
            return None
    
    def delete_search(self, search_id: str) -> bool:
        """Delete a search and its results
        
        Args:
            search_id: ID of the search to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            # Load history
            history = self.load_search_history()
            
            # Find and remove search record
            search_record = next((r for r in history if r["id"] == search_id), None)
            if not search_record:
                return False
            
            # Delete results file
            if "results_file" in search_record and os.path.exists(os.path.join(self.data_dir, search_record["results_file"])):
                os.remove(os.path.join(self.data_dir, search_record["results_file"]))
            
            # Update history
            history = [r for r in history if r["id"] != search_id]
            with open(self.search_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Failed to delete search: {str(e)}")
            return False
    
    def clear_history(self) -> bool:
        """Clear all search history and results
        
        Returns:
            bool: True if cleared successfully
        """
        try:
            # Delete all result files
            for file in os.listdir(self.results_dir):
                os.remove(os.path.join(self.results_dir, file))
            
            # Clear history file
            with open(self.search_file, 'w') as f:
                json.dump([], f)
            
            return True
            
        except Exception as e:
            print(f"Failed to clear history: {str(e)}")
            return False
    
    def repair_search_history(self) -> bool:
        """Repair and validate search history data
        
        Returns:
            bool: True if repair was successful
        """
        try:
            # Load current history
            history = self.load_search_history()
            if not history:
                # Initialize empty history if none exists
                with open(self.search_file, 'w') as f:
                    json.dump([], f, indent=2)
                return True
            
            valid_history = []
            for record in history:
                try:
                    # Validate record structure
                    if not isinstance(record, dict):
                        print(f"Skipping invalid record: {record}")
                        continue
                    
                    # Ensure required fields
                    required_fields = ["id", "timestamp", "query"]
                    if not all(field in record for field in required_fields):
                        print(f"Record missing required fields: {record}")
                        continue
                    
                    # Check results file
                    if "results_file" in record:
                        results_path = os.path.join(self.data_dir, record["results_file"])
                        if not os.path.exists(results_path):
                            print(f"Results file not found: {results_path}")
                            continue
                        
                        # Try to load and validate results
                        results = self.load_search_results(record["id"])
                        if results is None:
                            print(f"Invalid results data for ID: {record['id']}")
                            continue
                        
                        # Save validated results back to file
                        self.save_validated_results(record["id"], results)
                    
                    valid_history.append(record)
                    
                except Exception as e:
                    print(f"Error processing record: {str(e)}")
                    continue
            
            # Save validated history
            with open(self.search_file, 'w') as f:
                json.dump(valid_history, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Failed to repair search history: {str(e)}")
            return False
    
    def save_validated_results(self, search_id: str, results: List[Dict]) -> bool:
        """Save validated results data
        
        Args:
            search_id: ID of the search
            results: List of result dictionaries
            
        Returns:
            bool: True if save was successful
        """
        try:
            # Ensure results is a list of dictionaries
            if not isinstance(results, list):
                results = [results]
            
            # Validate each result
            validated_results = []
            for result in results:
                if not isinstance(result, dict):
                    continue
                    
                # Ensure required fields
                validated_result = {
                    "name": str(result.get("name", "")),
                    "title": str(result.get("title", "")),
                    "price": str(result.get("price", "")),
                    "rating": str(result.get("rating", "")),
                    "brand": str(result.get("brand", "")),
                    "link": str(result.get("link", "")),
                }
                validated_results.append(validated_result)
            
            # Save to JSON file
            results_file = os.path.join(self.results_dir, f"{search_id}.json")
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(validated_results, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Failed to save validated results: {str(e)}")
            return False
    
    def save_alternatives(self, original_product, alternatives, search_id=None):
        """Save alternatives for a product"""
        try:
            # Load existing alternatives
            alternatives_history = self.load_alternatives_history()
            
            # Create new alternatives record
            alternatives_record = {
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "search_id": search_id,
                "original_product": original_product,
                "alternatives": alternatives
            }
            
            # Add to history
            alternatives_history.append(alternatives_record)
            
            # Save updated history
            self.save_alternatives_history(alternatives_history)
            
            return alternatives_record["id"]
            
        except Exception as e:
            print(f"Error saving alternatives: {str(e)}")
            return None
    
    def load_alternatives_history(self):
        """Load alternatives history"""
        try:
            if os.path.exists(self.alternatives_file):
                with open(self.alternatives_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"Error loading alternatives history: {str(e)}")
            return []
    
    def save_alternatives_history(self, history):
        """Save alternatives history"""
        try:
            with open(self.alternatives_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving alternatives history: {str(e)}")
    
    def get_alternatives(self, alternatives_id):
        """Get alternatives by ID"""
        try:
            alternatives_history = self.load_alternatives_history()
            for record in alternatives_history:
                if record["id"] == alternatives_id:
                    return record["alternatives"]
            return None
        except Exception as e:
            print(f"Error getting alternatives: {str(e)}")
            return None
