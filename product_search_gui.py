import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                           QProgressBar, QTableWidget, QTableWidgetItem, 
                           QTabWidget, QMessageBox, QSplitter, QListWidget,
                           QCheckBox, QMenu, QHeaderView, QDialogButtonBox,
                           QDialog, QProgressDialog, QScrollArea, QFrame,
                           QSpinBox, QDoubleSpinBox, QGridLayout, QGroupBox,
                           QTreeWidget, QTreeWidgetItem)
from PySide6.QtCore import Qt, QThread, Signal, QPoint, QObject
from PySide6.QtGui import QTextCursor, QFont, QColor, QBrush
from batch_search import BatchSearcher
from ai_processor import AIProcessor
from data_store import SearchHistoryStore
import pandas as pd
import json
import time
from datetime import datetime
import csv
from urllib.parse import quote
from query_validator import QueryValidator

class LogTerminal(QTextEdit):
    """Custom terminal widget for logging"""
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                font-family: 'Consolas', 'Courier New', monospace;
                padding: 5px;
                border: 1px solid #333333;
            }
        """)
        font = QFont("Consolas", 9)
        self.setFont(font)

    def log(self, message: str, level: str = "info"):
        """Add a log message with timestamp and level"""
        timestamp = time.strftime("%H:%M:%S")
        color = {
            "info": "#FFFFFF",
            "success": "#00FF00",
            "error": "#FF0000",
            "warning": "#FFFF00"
        }.get(level, "#FFFFFF")
        
        formatted_message = f'<span style="color: #888888">[{timestamp}]</span> <span style="color: {color}">{message}</span><br>'
        self.moveCursor(QTextCursor.End)
        self.insertHtml(formatted_message)
        self.moveCursor(QTextCursor.End)

class SearchWorker(QObject):
    finished = Signal(list)
    error = Signal(str)
    progress = Signal(dict)
    
    def __init__(self, query: str):
        super().__init__()
        self.query = query
        self.searcher = BatchSearcher()
        self._stop = False
    
    def run(self):
        """Run the search operation"""
        try:
            # Update progress - Starting search
            self.progress.emit({
                "message": f"Starting search with query: {self.query}",
                "progress": 10
            })
            
            # Perform initial search
            self.progress.emit({
                "message": "Searching Amazon API...",
                "progress": 30
            })
            
            results = self.searcher.search(self.query)
            
            if self._stop:
                return
            
            if not results:
                self.progress.emit({
                    "message": "No results found",
                    "progress": 100
                })
                self.finished.emit([])
                return
            
            # Update progress - Processing results
            self.progress.emit({
                "message": f"Found {len(results)} results, processing...",
                "progress": 50
            })
            
            # Process each result
            processed_results = []
            total_results = len(results)
            
            for i, result in enumerate(results):
                if self._stop:
                    return
                
                # Update progress for each result
                progress = 50 + int((i + 1) / total_results * 40)
                self.progress.emit({
                    "message": f"Processing result {i + 1} of {total_results}...",
                    "progress": progress
                })
                
                processed_results.append(result)
                
                # Small delay to avoid overwhelming the UI
                QThread.msleep(50)
            
            # Final progress update
            self.progress.emit({
                "message": "Search completed successfully",
                "progress": 100
            })
            
            self.finished.emit(processed_results)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        """Stop the search operation"""
        self._stop = True
        if hasattr(self, 'searcher'):
            self.searcher.stop()

class QueryEnhanceWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, ai_processor, query):
        super().__init__()
        self.ai_processor = ai_processor
        self.query = query
    
    def run(self):
        """Run the query enhancement"""
        try:
            result = self.ai_processor.enhance_search_query(self.query)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class QueryValidateWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, validator, query):
        super().__init__()
        self.validator = validator
        self.query = query
    
    def run(self):
        """Run the query validation"""
        try:
            result = self.validator.validate_query(self.query)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class NonProductQueryWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, validator, query, category):
        super().__init__()
        self.validator = validator
        self.query = query
        self.category = category
    
    def run(self):
        """Handle the non-product query"""
        try:
            result = self.validator.handle_non_product_query(self.query, self.category)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class SuggestionsDialog(QDialog):
    def __init__(self, suggestions: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Suggestions")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Add suggestions label
        label = QLabel("Here are some suggestions to improve your search:")
        layout.addWidget(label)
        
        # Add suggestions list
        suggestions_list = QListWidget()
        for suggestion in suggestions:
            suggestions_list.addItem(suggestion)
        layout.addWidget(suggestions_list)
        
        # Add buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

class NonProductResponseDialog(QDialog):
    def __init__(self, response_data, parent=None):
        super().__init__(parent)
        self.response_data = response_data
        self.init_ui()
    
    def init_ui(self):
        """Initialize the dialog UI"""
        self.setWindowTitle(f"Response - {self.response_data['category'].title()}")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Add response text
        response_text = QTextEdit()
        response_text.setReadOnly(True)
        response_text.setText(self.response_data['response'])
        layout.addWidget(response_text)
        
        # Add close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)

class ProductCompareTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Add description label
        description = QLabel("Select products to compare their specifications and find alternatives.")
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Create splitter for products and comparison
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Product selection
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Product selection table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(3)
        self.products_table.setHorizontalHeaderLabels(["Select", "Product", "Price"])
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        left_layout.addWidget(self.products_table)
        
        # Compare button
        compare_btn = QPushButton("Compare Selected")
        compare_btn.clicked.connect(self.compare_products)
        left_layout.addWidget(compare_btn)
        
        splitter.addWidget(left_widget)
        
        # Right side - Comparison results
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(0)  # Will be set dynamically
        self.comparison_table.setHorizontalHeaderLabels([])
        self.comparison_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        splitter.addWidget(self.comparison_table)
        
        # Set splitter sizes
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
    
    def compare_products(self):
        selected_products = []
        for row in range(self.products_table.rowCount()):
            checkbox = self.products_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                product_name = self.products_table.item(row, 1).text()
                selected_products.append(product_name)
        
        if len(selected_products) < 2:
            QMessageBox.warning(self, "Warning", "Please select at least 2 products to compare.")
            return
            
        # Get detailed specifications for each product
        specs = self._get_product_specs(selected_products)
        self._display_comparison(specs)
    
    def _get_product_specs(self, products):
        # This would fetch detailed specifications from your data source
        # For now, returning dummy data
        specs = {}
        for product in products:
            specs[product] = {
                "Price": "$999.99",
                "Rating": "4.5/5",
                "Dimensions": "12 x 5 x 3 inches",
                "Weight": "2.5 lbs",
                "Brand": "Example Brand",
                "Model": "ABC123",
                "Release Date": "2024",
                "Warranty": "1 year"
            }
        return specs
    
    def _display_comparison(self, specs):
        if not specs:
            return
            
        # Get all unique specification keys
        all_specs = set()
        for product_specs in specs.values():
            all_specs.update(product_specs.keys())
        
        # Set up table
        products = list(specs.keys())
        self.comparison_table.setColumnCount(len(products))
        self.comparison_table.setHorizontalHeaderLabels(products)
        self.comparison_table.setRowCount(len(all_specs))
        self.comparison_table.setVerticalHeaderLabels(list(all_specs))
        
        # Fill in specifications
        for col, product in enumerate(products):
            for row, spec in enumerate(all_specs):
                value = specs[product].get(spec, "N/A")
                item = QTableWidgetItem(str(value))
                self.comparison_table.setItem(row, col, item)

class AlternativesTab(QWidget):
    def __init__(self, data_store, parent=None):
        super().__init__(parent)
        self.data_store = data_store
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Add description label
        description = QLabel("Select products to find alternatives for:")
        main_layout.addWidget(description)
        
        # Create product selection table
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(3)
        self.product_table.setHorizontalHeaderLabels(["Select", "Name", "Price"])
        self.product_table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.product_table)
        
        # Add find alternatives button
        self.find_button = QPushButton("Find Alternatives")
        self.find_button.clicked.connect(self.find_alternatives)
        main_layout.addWidget(self.find_button)
        
        # Add alternatives table
        self.alternatives_table = QTableWidget()
        self.alternatives_table.setColumnCount(5)
        self.alternatives_table.setHorizontalHeaderLabels(["Name", "Price", "Rating", "Link", "Select"])
        self.alternatives_table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.alternatives_table)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Add save button
        self.save_button = QPushButton("Save Alternatives")
        self.save_button.clicked.connect(self.save_alternatives)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)
        
        # Add export button
        self.export_button = QPushButton("Export Selected Alternatives")
        self.export_button.clicked.connect(self.export_alternatives)
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def find_alternatives(self):
        """Find alternatives for selected products"""
        try:
            # Get selected products
            selected_products = []
            for row in range(self.product_table.rowCount()):
                checkbox = self.product_table.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    # Get price and clean it
                    price_text = self.product_table.item(row, 2).text() if self.product_table.item(row, 2) else "0"
                    # Remove currency symbols and convert to float safely
                    try:
                        price = float(price_text.replace('$', '').replace(',', '').strip())
                    except (ValueError, AttributeError):
                        price = 0.0
                        
                    product = {
                        "name": self.product_table.item(row, 1).text() if self.product_table.item(row, 1) else "",
                        "price": price,  # Store as float
                        "original_link": self.window().results_table.item(row, 6).text() if self.window().results_table.item(row, 6) else ""
                    }
                    selected_products.append(product)
            
            if not selected_products:
                QMessageBox.warning(self, "Warning", "Please select at least one product to find alternatives")
                return
            
            # Create and show progress dialog
            progress = QProgressDialog("Finding alternatives...", "Cancel", 0, len(selected_products), self)
            progress.setWindowTitle("Finding Alternatives")
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            
            # Process each product
            alternatives = []
            for i, product in enumerate(selected_products):
                if progress.wasCanceled():
                    break
                    
                # Update progress
                progress.setValue(i)
                progress.setLabelText(f"Finding alternatives for {product['name']}")
                
                # Extract product category and key terms
                product_terms = product['name'].lower().split()
                
                # Generate search terms for alternatives
                search_terms = []
                if "gpu" in product_terms or "graphics" in product_terms:
                    search_terms = ["GPU", "Graphics Card", "Video Card"]
                elif "motherboard" in product_terms:
                    search_terms = ["Motherboard", "Gaming Motherboard", "ATX Motherboard"]
                elif "ram" in product_terms or "memory" in product_terms:
                    search_terms = ["RAM", "DDR4", "Memory"]
                elif "psu" in product_terms or "power supply" in product_terms:
                    search_terms = ["Power Supply", "PSU", "ATX Power"]
                elif "cooler" in product_terms or "cooling" in product_terms:
                    search_terms = ["CPU Cooler", "Liquid Cooling", "Air Cooler"]
                else:
                    search_terms = ["PC Component", "Computer Part"]
                
                # Generate alternatives with proper links
                base_price = product['price']
                for j in range(3):
                    # Create search term for this alternative
                    search_term = search_terms[j % len(search_terms)]
                    # Create Amazon search link
                    encoded_search = quote(f"{search_term} alternative to {product['name']}")
                    amazon_link = f"https://www.amazon.com/s?k={encoded_search}"
                    
                    alternatives.append({
                        "name": f"Alternative {j+1}: {search_term} similar to {product['name']}",
                        "price": f"${base_price * (0.8 + (j * 0.1)):.2f}",  # Vary price by 10% increments
                        "rating": "4.5",
                        "link": amazon_link
                    })
                
            # Close progress dialog
            progress.setValue(len(selected_products))
            
            # Display alternatives
            if alternatives:
                self.display_alternatives(alternatives)
                if hasattr(self.window(), 'terminal'):
                    self.window().terminal.log(f"Found {len(alternatives)} alternatives", "success")
            else:
                if hasattr(self.window(), 'terminal'):
                    self.window().terminal.log("No alternatives found", "warning")
            
        except Exception as e:
            if hasattr(self.window(), 'terminal'):
                self.window().terminal.log(f"Error finding alternatives: {str(e)}", "error")
            QMessageBox.critical(self, "Error", f"Error finding alternatives: {str(e)}")
    
    def display_alternatives(self, alternatives, original_product=None):
        """Display alternatives in the table"""
        try:
            # Store the alternatives and original product for saving later
            self.current_alternatives = alternatives
            self.current_original_product = original_product
            
            # Clear existing alternatives
            self.alternatives_table.clearContents()
            self.alternatives_table.setRowCount(0)
            
            if not alternatives:
                return
                
            # Set up table
            headers = ["Name", "Price", "Rating", "Link", "Select"]
            self.alternatives_table.setColumnCount(len(headers))
            self.alternatives_table.setHorizontalHeaderLabels(headers)
            
            # Add alternatives to table
            self.alternatives_table.setRowCount(len(alternatives))
            for row, alt in enumerate(alternatives):
                # Add name
                name_item = QTableWidgetItem(str(alt.get("name", "")))
                self.alternatives_table.setItem(row, 0, name_item)
                
                # Add price
                price_item = QTableWidgetItem(str(alt.get("price", "")))
                self.alternatives_table.setItem(row, 1, price_item)
                
                # Add rating
                rating_item = QTableWidgetItem(str(alt.get("rating", "")))
                self.alternatives_table.setItem(row, 2, rating_item)
                
                # Add link as clickable
                link = alt.get("link", "")
                link_item = QTableWidgetItem(link)
                link_item.setForeground(QBrush(QColor("blue")))
                self.alternatives_table.setItem(row, 3, link_item)
                
                # Add checkbox
                checkbox = QCheckBox()
                self.alternatives_table.setCellWidget(row, 4, checkbox)
            
            # Resize columns to content
            self.alternatives_table.resizeColumnsToContents()
            
            # Enable buttons
            self.save_button.setEnabled(True)
            self.export_button.setEnabled(True)
            
            if hasattr(self.window(), 'terminal'):
                self.window().terminal.log(f"Displayed {len(alternatives)} alternatives", "success")
                
        except Exception as e:
            if hasattr(self.window(), 'terminal'):
                self.window().terminal.log(f"Error displaying alternatives: {str(e)}", "error")
    
    def save_alternatives(self):
        """Save current alternatives to history"""
        try:
            if not hasattr(self, 'current_alternatives') or not self.current_alternatives:
                QMessageBox.warning(self, "Warning", "No alternatives to save")
                return
                
            # Get current search ID if available
            search_id = None
            if hasattr(self.window(), 'current_search_id'):
                search_id = self.window().current_search_id
            
            # Save alternatives
            alternatives_id = self.data_store.save_alternatives(
                self.current_original_product,
                self.current_alternatives,
                search_id
            )
            
            if alternatives_id:
                if hasattr(self.window(), 'terminal'):
                    self.window().terminal.log(f"Saved alternatives with ID: {alternatives_id}", "success")
                QMessageBox.information(self, "Success", "Alternatives saved successfully!")
            else:
                if hasattr(self.window(), 'terminal'):
                    self.window().terminal.log("Failed to save alternatives", "error")
                QMessageBox.warning(self, "Error", "Failed to save alternatives")
            
        except Exception as e:
            if hasattr(self.window(), 'terminal'):
                self.window().terminal.log(f"Error saving alternatives: {str(e)}", "error")
            QMessageBox.critical(self, "Error", f"Error saving alternatives: {str(e)}")
    
    def export_alternatives(self):
        """Export selected alternatives to CSV"""
        try:
            # Get selected alternatives
            selected_alternatives = []
            for row in range(self.alternatives_table.rowCount()):
                checkbox = self.alternatives_table.cellWidget(row, 4)
                if checkbox and checkbox.isChecked():
                    alt = {
                        "name": self.alternatives_table.item(row, 0).text() if self.alternatives_table.item(row, 0) else "",
                        "price": self.alternatives_table.item(row, 1).text() if self.alternatives_table.item(row, 1) else "",
                        "rating": self.alternatives_table.item(row, 2).text() if self.alternatives_table.item(row, 2) else "",
                        "link": self.alternatives_table.item(row, 3).text() if self.alternatives_table.item(row, 3) else ""
                    }
                    selected_alternatives.append(alt)
            
            if not selected_alternatives:
                QMessageBox.warning(self, "Warning", "Please select at least one alternative to export")
                return
            
            # Export to CSV
            filename = "alternatives.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                # Write headers
                headers = ["Name", "Price", "Rating", "Link"]
                writer.writerow(headers)
                
                # Write data
                for alt in selected_alternatives:
                    writer.writerow([alt["name"], alt["price"], alt["rating"], alt["link"]])
                    
            if hasattr(self.window(), 'terminal'):
                self.window().terminal.log(f"Exported {len(selected_alternatives)} alternatives to {filename}", "success")
            QMessageBox.information(self, "Success", f"Exported {len(selected_alternatives)} alternatives to {filename}")
            
        except Exception as e:
            if hasattr(self.window(), 'terminal'):
                self.window().terminal.log(f"Error exporting alternatives: {str(e)}", "error")
            QMessageBox.critical(self, "Error", f"Error exporting alternatives: {str(e)}")

    def populate_products(self):
        """Populate products table with results from previous search"""
        try:
            # Get main window
            main_window = self.window()
            
            # Get results from previous search
            results = main_window.results_table
            
            # Clear existing products
            self.product_table.clearContents()
            self.product_table.setRowCount(0)
            
            # Set up table
            headers = ["Select", "Name", "Price"]
            self.product_table.setColumnCount(len(headers))
            self.product_table.setHorizontalHeaderLabels(headers)
            
            # Add results to table
            self.product_table.setRowCount(results.rowCount())
            for row in range(results.rowCount()):
                # Add checkbox
                checkbox = QCheckBox()
                self.product_table.setCellWidget(row, 0, checkbox)
                
                # Add name
                name_item = QTableWidgetItem(results.item(row, 1).text() if results.item(row, 1) else "")
                self.product_table.setItem(row, 1, name_item)
                
                # Add price
                price_item = QTableWidgetItem(results.item(row, 3).text() if results.item(row, 3) else "")
                self.product_table.setItem(row, 2, price_item)
            
            # Resize columns to content
            self.product_table.resizeColumnsToContents()
            
            if hasattr(self.window(), 'terminal'):
                self.window().terminal.log("Loaded products for alternatives", "info")
                
        except Exception as e:
            if hasattr(self.window(), 'terminal'):
                self.window().terminal.log(f"Error loading products: {str(e)}", "error")

class SearchHistoryTab(QWidget):
    def __init__(self, data_store: SearchHistoryStore, parent=None):
        super().__init__(parent)
        self.data_store = data_store
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tree widget for history
        self.history_tree = QTreeWidget()
        self.history_tree.setHeaderLabels(["Date/Time", "Query", "Results"])
        self.history_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_tree.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.history_tree)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Load Search button
        self.load_btn = QPushButton("Load Selected Search")
        self.load_btn.clicked.connect(self.load_selected_search)
        button_layout.addWidget(self.load_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh History")
        self.refresh_btn.clicked.connect(self.load_history)
        button_layout.addWidget(self.refresh_btn)
        
        # Clear button
        self.clear_btn = QPushButton("Clear History")
        self.clear_btn.clicked.connect(self.clear_history)
        button_layout.addWidget(self.clear_btn)
        
        layout.addLayout(button_layout)
        
        # Load initial history
        self.load_history()
    
    def load_history(self):
        """Load and display search history"""
        self.history_tree.clear()
        history = self.data_store.load_search_history()
        
        for record in sorted(history, key=lambda x: x["timestamp"], reverse=True):
            item = QTreeWidgetItem([
                datetime.fromisoformat(record["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
                record["query"],
                str(record["result_count"]) + " results"
            ])
            item.setData(0, Qt.UserRole, record["id"])
            self.history_tree.addTopLevelItem(item)
        
        self.history_tree.resizeColumnToContents(0)
        self.history_tree.resizeColumnToContents(1)
    
    def load_selected_search(self):
        """Load the selected search into the main application"""
        selected_items = self.history_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a search from history")
            return
        
        try:
            # Get the search ID from the selected item
            search_id = selected_items[0].data(0, Qt.UserRole)
            
            # Get main window
            main_window = self.window()
            
            # Load search results
            results = self.data_store.load_search_results(search_id)
            if results is not None:
                # Set the search query in the input tab
                query = selected_items[0].text(1)
                main_window.input_text.setPlainText(query)
                
                # Display results
                main_window.display_results(results)
                
                # Switch to results tab
                main_window.tabs.setCurrentIndex(1)
                
                main_window.terminal.log(f"Loaded search results from history", "success")
            else:
                QMessageBox.warning(self, "Error", "Failed to load search results")
                main_window.terminal.log("Failed to load search results", "error")
                
        except Exception as e:
            error_msg = f"Failed to load search: {str(e)}"
            QMessageBox.warning(self, "Error", error_msg)
            if hasattr(self.window(), 'terminal'):
                self.window().terminal.log(error_msg, "error")
    
    def show_context_menu(self, position: QPoint):
        """Show context menu for history items"""
        item = self.history_tree.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        load_action = menu.addAction("Load Results")
        delete_action = menu.addAction("Delete")
        
        action = menu.exec(self.history_tree.viewport().mapToGlobal(position))
        if not action:
            return
        
        search_id = item.data(0, Qt.UserRole)
        
        if action == load_action:
            # Use the same loading logic
            self.load_selected_search()
                
        elif action == delete_action:
            if self.data_store.delete_search(search_id):
                self.load_history()
                self.window().terminal.log(f"Deleted search from history", "info")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete search")
    
    def clear_history(self):
        """Clear all search history"""
        reply = QMessageBox.question(
            self, "Clear History",
            "Are you sure you want to clear all search history?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.data_store.clear_history():
                self.load_history()
                self.window().terminal.log("Cleared search history", "info")
            else:
                QMessageBox.warning(self, "Error", "Failed to clear history")

class ProductSearchUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Amazon Product Search")
        self.resize(1200, 800)
        
        # Initialize components
        self.data_store = SearchHistoryStore()
        self.ai_processor = AIProcessor()
        self.query_validator = QueryValidator()
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        self.init_ui()
        
        # Create progress indicator
        self.progress = None
        
        # Create search worker
        self.search_worker = None
        self.search_thread = None
    
    def init_ui(self):
        """Initialize the UI components"""
        # Create main widget and layout
        main_layout = self.centralWidget().layout()
        
        # Create horizontal splitter for main content and terminal
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create left widget for main content
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Input tab
        input_tab = QWidget()
        input_layout = QVBoxLayout(input_tab)
        
        # Add input text area
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("Enter search query here...")
        input_layout.addWidget(self.input_text)
        
        # Add search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_products)
        input_layout.addWidget(self.search_button)
        
        # Results tab
        results_tab = QWidget()
        results_layout = QVBoxLayout(results_tab)
        
        # Add results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels([
            "Select", "Name", "Title", "Price", "Rating", "Brand", "Link"
        ])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        results_layout.addWidget(self.results_table)
        
        # Add export button
        self.export_button = QPushButton("Export Results")
        self.export_button.clicked.connect(self.export_results)
        self.export_button.setEnabled(False)
        results_layout.addWidget(self.export_button)
        
        # Add tabs
        self.tabs.addTab(input_tab, "Input")
        self.tabs.addTab(results_tab, "Results")
        
        # Add History tab
        history_tab = SearchHistoryTab(self.data_store)
        self.tabs.addTab(history_tab, "History")
        
        # Add Compare tab
        compare_tab = ProductCompareTab()
        self.tabs.addTab(compare_tab, "Compare")
        
        # Create Alternatives tab
        self.alternatives_tab = AlternativesTab(self.data_store)
        self.tabs.addTab(self.alternatives_tab, "Alternatives")
        
        # Add tabs to left layout
        left_layout.addWidget(self.tabs)
        left_widget.setLayout(left_layout)
        
        # Add left widget to splitter
        splitter.addWidget(left_widget)
        
        # Create right widget for terminal
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Add terminal label
        terminal_label = QLabel("Terminal Output")
        terminal_label.setStyleSheet("color: #CCCCCC; background-color: #2D2D2D; padding: 5px;")
        right_layout.addWidget(terminal_label)
        
        # Create and add terminal
        self.terminal = LogTerminal()
        right_layout.addWidget(self.terminal)
        
        # Add right widget to splitter
        splitter.addWidget(right_widget)
        
        # Set splitter proportions (70% left, 30% right)
        splitter.setSizes([700, 300])
        
        # Connect tab change handler
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
        # Initial terminal message
        self.terminal.log("Terminal ready. Waiting for input...", "info")
        
        # Repair data store after terminal is created
        self.repair_data_store()
        
    def update_search_progress(self, progress_data):
        """Update the search progress"""
        try:
            message = progress_data.get('message', '')
            progress = progress_data.get('progress', 0)
            
            if self.progress is None:
                self.progress = QProgressDialog("Searching...", "Cancel", 0, 100, self)
                self.progress.setWindowModality(Qt.WindowModal)
                self.progress.setAutoClose(True)
                self.progress.canceled.connect(self.cancel_search)
            
            self.progress.setLabelText(message)
            self.progress.setValue(progress)
            
        except Exception as e:
            self.terminal.log(f"Error updating progress: {str(e)}", "error")
    
    def cancel_search(self):
        """Cancel the current search operation"""
        try:
            if self.search_worker:
                self.search_worker.stop()
                self.terminal.log("Search cancelled by user", "warning")
        except Exception as e:
            self.terminal.log(f"Error cancelling search: {str(e)}", "error")
    
    def get_ai_suggestions(self):
        """Get AI suggestions for the current input"""
        current_input = self.input_text.toPlainText().strip()
        if not current_input:
            QMessageBox.warning(self, "Warning", "Please enter some search text first")
            return
        
        self.terminal.log("Getting AI suggestions...", "info")
        suggestions = self.ai_processor.get_search_suggestions(current_input)
        
        dialog = SuggestionsDialog(suggestions, self)
        if dialog.exec() == QDialog.Accepted:
            self.terminal.log("Applying AI suggestions...", "info")
            # Process the input with AI
            try:
                processed_data = self.ai_processor.process_user_input(current_input)
                if "error" not in processed_data:
                    # Format the processed data back into text
                    formatted_text = json.dumps(processed_data, indent=2)
                    self.input_text.setPlainText(formatted_text)
                    self.terminal.log("Input processed and formatted by AI", "success")
                else:
                    self.terminal.log(f"AI processing error: {processed_data['error']}", "error")
            except Exception as e:
                self.terminal.log(f"Failed to process input: {str(e)}", "error")
    
    def search_products(self):
        """Start the product search process"""
        try:
            query = self.input_text.toPlainText().strip()
            if not query:
                QMessageBox.warning(self, "Warning", "Please enter a search query")
                return
            
            # Disable search button
            self.search_button.setEnabled(False)
            
            try:
                # Try validation first
                self.terminal.log("Validating query...", "info")
                validation_result = self.query_validator.validate_query(query)
                
                if validation_result.get('is_product_search', True):
                    # Use enhanced query if available
                    enhanced_query = validation_result.get('enhanced_query', query)
                    self.terminal.log(f"Enhanced query: {enhanced_query}", "info")
                    self.start_product_search(enhanced_query)
                else:
                    # Handle non-product query
                    self.terminal.log("This appears to be a non-product query", "warning")
                    self.handle_non_product_query(validation_result)
                    
            except Exception as e:
                # Validation failed, fall back to direct API search
                self.terminal.log(f"Validation error: {str(e)}", "warning")
                self.terminal.log("Falling back to direct API search...", "info")
                
                # Enhance query for API search
                enhanced_query = self.enhance_query_for_api(query)
                self.start_product_search(enhanced_query)
            
        except Exception as e:
            self.terminal.log(f"Error starting search: {str(e)}", "error")
            self.search_button.setEnabled(True)
    
    def handle_validated_query(self, validation_result):
        """Handle the validated query result"""
        try:
            # Log the validation result
            self.terminal.log(f"Query category: {validation_result['category']}", "info")
            
            if validation_result['is_product_search']:
                # Product search
                self.terminal.log(f"Enhanced query: {validation_result['enhanced_query']}", "info")
                self.terminal.log(f"Suggestion: {validation_result['suggestion']}", "info")
                self.terminal.log(validation_result['explanation'], "info")
                
                # Start the product search
                self.start_product_search(validation_result['enhanced_query'])
            else:
                # Non-product query
                self.terminal.log("This appears to be a non-product query", "warning")
                self.terminal.log(validation_result['explanation'], "info")
                
                # Handle non-product query
                self.handle_non_product_query(validation_result)
            
        except Exception as e:
            self.terminal.log(f"Error handling validated query: {str(e)}", "error")
            self.search_button.setEnabled(True)
    
    def handle_validate_error(self, error_message):
        """Handle query validation error by falling back to direct API search"""
        self.terminal.log(f"Query validation failed: {error_message}", "warning")
        self.terminal.log("Falling back to direct API search...", "info")
        
        # Continue with original query
        query = self.input_text.toPlainText().strip()
        
        # Enhance query for API search
        enhanced_query = self.enhance_query_for_api(query)
        self.start_product_search(enhanced_query)
    
    def enhance_query_for_api(self, query):
        """Enhance query for API search by adding relevant keywords"""
        try:
            # Add product-specific keywords if not present
            keywords = ["product", "buy", "amazon"]
            query_lower = query.lower()
            
            # Check if query needs enhancement
            needs_enhancement = not any(kw in query_lower for kw in keywords)
            
            if needs_enhancement:
                # Add "product" to make it more product-focused
                enhanced = f"{query} product"
                self.terminal.log(f"Enhanced query: {enhanced}", "info")
                return enhanced
            
            return query
            
        except Exception as e:
            self.terminal.log(f"Error enhancing query: {str(e)}", "error")
            return query
    
    def handle_non_product_query(self, validation_result):
        """Handle non-product queries"""
        try:
            # Create a worker thread for non-product query handling
            self.non_product_thread = QThread()
            self.non_product_worker = NonProductQueryWorker(
                self.query_validator,
                self.input_text.toPlainText().strip(),
                validation_result['category']
            )
            self.non_product_worker.moveToThread(self.non_product_thread)
            
            # Connect signals
            self.non_product_thread.started.connect(self.non_product_worker.run)
            self.non_product_worker.finished.connect(self.display_non_product_response)
            self.non_product_worker.error.connect(self.handle_non_product_error)
            
            # Start handling
            self.non_product_thread.start()
            
        except Exception as e:
            self.terminal.log(f"Error handling non-product query: {str(e)}", "error")
            self.search_button.setEnabled(True)
    
    def display_non_product_response(self, response_data):
        """Display response for non-product queries"""
        try:
            # Create and show dialog with response
            dialog = NonProductResponseDialog(response_data, self)
            dialog.exec_()
            
            # Re-enable search button
            self.search_button.setEnabled(True)
            
        except Exception as e:
            self.terminal.log(f"Error displaying non-product response: {str(e)}", "error")
            self.search_button.setEnabled(True)
    
    def start_product_search(self, query):
        """Start the actual product search with the given query"""
        try:
            # Create and setup search worker
            self.search_thread = QThread()
            self.search_worker = SearchWorker(query)
            self.search_worker.moveToThread(self.search_thread)
            
            # Connect signals
            self.search_thread.started.connect(self.search_worker.run)
            self.search_worker.finished.connect(self.handle_search_results)
            self.search_worker.error.connect(self.handle_search_error)
            self.search_worker.progress.connect(self.update_search_progress)
            
            # Start search
            self.terminal.log(f"Starting search with query: {query}", "info")
            self.search_thread.start()
            
        except Exception as e:
            self.terminal.log(f"Error starting search: {str(e)}", "error")
            self.search_button.setEnabled(True)
    
    def handle_search_results(self, results):
        """Handle the search results"""
        try:
            if not results:
                self.terminal.log("No results found", "warning")
                self.search_button.setEnabled(True)
                return
            
            # Update results table
            self.results_table.setRowCount(len(results))
            for i, result in enumerate(results):
                # Add checkbox
                checkbox = QCheckBox()
                self.results_table.setCellWidget(i, 0, checkbox)
                
                # Add other data
                self.results_table.setItem(i, 1, QTableWidgetItem(result.get("name", "")))
                self.results_table.setItem(i, 2, QTableWidgetItem(result.get("title", "")))
                self.results_table.setItem(i, 3, QTableWidgetItem(result.get("price", "")))
                self.results_table.setItem(i, 4, QTableWidgetItem(result.get("rating", "")))
                self.results_table.setItem(i, 5, QTableWidgetItem(result.get("brand", "")))
                self.results_table.setItem(i, 6, QTableWidgetItem(result.get("url", "")))
            
            # Enable export button
            self.export_button.setEnabled(True)
            
            # Switch to results tab
            self.tabs.setCurrentIndex(1)
            
            # Store search in history
            self.data_store.add_search_history({
                "query": self.input_text.toPlainText().strip(),
                "timestamp": datetime.now().isoformat(),
                "results": results
            })
            
        except Exception as e:
            self.terminal.log(f"Error handling results: {str(e)}", "error")
        finally:
            self.search_button.setEnabled(True)
            
    def handle_search_error(self, error_message):
        """Handle search error"""
        self.terminal.log(f"Search error: {error_message}", "error")
        self.search_button.setEnabled(True)
    
    def display_results(self, results):
        """Display search results in the table"""
        try:
            # Clear existing results
            self.results_table.clearContents()
            self.results_table.setRowCount(0)
            
            if not results:
                return
                
            # Set up table
            headers = ["Select", "Name", "Title", "Price", "Rating", "Brand", "Link"]
            self.results_table.setColumnCount(len(headers))
            self.results_table.setHorizontalHeaderLabels(headers)
            
            # Add select all checkbox to header
            select_all_checkbox = QCheckBox()
            select_all_checkbox.stateChanged.connect(self.toggle_all_selections)
            header = self.results_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            self.results_table.setHorizontalHeaderItem(0, QTableWidgetItem("Select"))
            
            # Add results
            self.results_table.setRowCount(len(results))
            for row, result in enumerate(results):
                # Add checkbox in first column
                checkbox = QCheckBox()
                self.results_table.setCellWidget(row, 0, checkbox)
                
                # Add other data
                self.results_table.setItem(row, 1, QTableWidgetItem(str(result.get("name", ""))))
                self.results_table.setItem(row, 2, QTableWidgetItem(str(result.get("title", ""))))
                self.results_table.setItem(row, 3, QTableWidgetItem(str(result.get("price", ""))))
                self.results_table.setItem(row, 4, QTableWidgetItem(str(result.get("rating", ""))))
                self.results_table.setItem(row, 5, QTableWidgetItem(str(result.get("brand", ""))))
                
                # Add link as clickable
                link = result.get("link", "")
                link_item = QTableWidgetItem(link)
                link_item.setForeground(QBrush(QColor("blue")))
                self.results_table.setItem(row, 6, link_item)
            
            # Resize columns to content
            self.results_table.resizeColumnsToContents()
            
            # Enable export button if it exists
            if hasattr(self, 'export_button'):
                self.export_button.setEnabled(True)
            
            # Switch to results tab
            self.tabs.setCurrentIndex(1)
            
            # Log success
            self.terminal.log(f"Displayed {len(results)} results", "success")
            
        except Exception as e:
            error_msg = f"Error displaying results: {str(e)}"
            self.terminal.log(error_msg, "error")
            QMessageBox.warning(self, "Error", error_msg)
            
    def toggle_all_selections(self, state):
        """Toggle all checkboxes in results table"""
        try:
            for row in range(self.results_table.rowCount()):
                checkbox = self.results_table.cellWidget(row, 0)
                if checkbox and isinstance(checkbox, QCheckBox):
                    checkbox.setChecked(state == Qt.Checked)
        except Exception as e:
            self.terminal.log(f"Error toggling selections: {str(e)}", "error")
            
    def export_results(self):
        """Export results to CSV"""
        try:
            filename = "product_results.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                # Write headers
                headers = [self.results_table.horizontalHeaderItem(i).text() 
                          for i in range(self.results_table.columnCount())]
                writer.writerow(headers)
                
                # Write data
                for row in range(self.results_table.rowCount()):
                    row_data = []
                    for col in range(self.results_table.columnCount()):
                        if col == 0:  # Checkbox column
                            checkbox = self.results_table.cellWidget(row, col)
                            row_data.append("Selected" if checkbox and checkbox.isChecked() else "")
                        else:
                            item = self.results_table.item(row, col)
                            row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
                    
            self.terminal.log(f"Results exported to {filename}", "success")
            QMessageBox.information(self, "Success", f"Results exported to {filename}")
            
        except Exception as e:
            error_msg = f"Failed to export results: {str(e)}"
            self.terminal.log(error_msg, "error")
            QMessageBox.critical(self, "Error", error_msg)

    def load_search_results(self, search_id):
        """Load search results from history"""
        try:
            results = self.data_store.load_search_results(search_id)
            if results is not None:
                # Handle different result formats
                if isinstance(results, str):
                    try:
                        # Try to parse JSON first
                        results = json.loads(results)
                    except json.JSONDecodeError:
                        try:
                            # Fallback to safer eval for string representations
                            import ast
                            results = ast.literal_eval(results)
                        except (SyntaxError, ValueError):
                            self.terminal.log("Failed to parse results data", "error")
                            return None
                
                # Ensure results is a list
                if not isinstance(results, list):
                    results = [results]
                
                return results
            
            self.terminal.log("No results found", "warning")
            return None
            
        except Exception as e:
            self.terminal.log(f"Error loading search results: {str(e)}", "error")
            return None

    def on_tab_changed(self, index):
        """Handle tab change"""
        try:
            # Get the current tab
            current_tab = self.tabs.widget(index)
            
            # If switching to Alternatives tab, populate products
            if isinstance(current_tab, AlternativesTab):
                current_tab.populate_products()
                self.terminal.log("Loaded products for alternatives", "info")
            
        except Exception as e:
            self.terminal.log(f"Error handling tab change: {str(e)}", "error")

    def repair_data_store(self):
        """Repair data store on startup"""
        try:
            self.terminal.log("Checking and repairing data store...", "info")
            if self.data_store.repair_search_history():
                self.terminal.log("Data store check completed", "success")
            else:
                self.terminal.log("Failed to repair data store", "error")
        except Exception as e:
            self.terminal.log(f"Error during data store repair: {str(e)}", "error")

def main():
    app = QApplication(sys.argv)
    window = ProductSearchUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
