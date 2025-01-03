import sys
import os
from PySide6.QtWidgets import QApplication, QMessageBox
from product_search_gui import ProductSearchUI

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API key (https://platform.openai.com/account/api-keys)',
        'RAPIDAPI_KEY': 'RapidAPI key (https://rapidapi.com/)',
        'GOOGLE_API_KEY': 'Google API key (https://console.cloud.google.com/)',
        'GOOGLE_SEARCH_ENGINE_ID': 'Google Search Engine ID (https://programmablesearchengine.google.com/)'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} - {description}")
    
    if missing_vars:
        error_msg = "Missing required environment variables:\n"
        error_msg += "\n".join(missing_vars)
        error_msg += "\n\nPlease check the README.md file for setup instructions."
        raise EnvironmentError(error_msg)

def main():
    # Check environment variables
    check_environment()
    
    # Create the Qt Application
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = ProductSearchUI()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Show error in GUI dialog
        error_app = QApplication(sys.argv)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error Starting Application")
        msg.setInformativeText(str(e))
        msg.setWindowTitle("Error")
        msg.exec_()
        sys.exit(1)
