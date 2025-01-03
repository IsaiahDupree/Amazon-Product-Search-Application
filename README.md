# Amazon Product Search Application

An intelligent product search application that combines Amazon's product data with AI-powered query understanding. This application leverages OpenAI's GPT models, Google Search, and Amazon's product data to provide smart, context-aware product searches.

## 🌟 Features

### Smart Search Capabilities
- **AI-Powered Query Understanding**
  - Natural language query processing
  - Context-aware search enhancement
  - Automatic query refinement
  - Non-product query handling

### Product Search
- **Amazon Product Integration**
  - Real-time product data
  - Price comparison
  - Product details and specifications
  - Related product suggestions

### Advanced Features
- **Multi-Source Intelligence**
  - OpenAI GPT integration
  - Google Search enhancement
  - Amazon product data
  - Smart fallback mechanisms

- **User Experience**
  - Modern Qt-based GUI
  - Real-time search updates
  - Progress tracking
  - Error handling and recovery

## 🛠️ Technical Architecture

### Components
1. **GUI Layer** (`product_search_gui.py`)
   - Qt-based user interface
   - Search input handling
   - Results display
   - Progress updates

2. **Search Logic** (`batch_search.py`)
   - Batch processing
   - Result aggregation
   - Error handling

3. **API Integration**
   - `amazon_api_client.py`: Amazon product data
   - `google_search_client.py`: Search enhancement
   - `query_validator.py`: Query processing

4. **Data Management**
   - `data_store.py`: Local data handling
   - Search history tracking
   - Result caching

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Qt development environment
- Required API keys (see below)

### Installation

1. **Clone the Repository**
```bash
git clone https://github.com/IsaiahDupree/Amazon-Product-Search-Application.git
cd Amazon-Product-Search-Application
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Set Up Environment Variables**
```bash
cp .env.template .env
# Edit .env with your API keys
```

### Required API Keys
- **OpenAI API Key**: For query understanding
  - Get from: https://platform.openai.com/account/api-keys
  
- **RapidAPI Key**: For Amazon product data
  - Get from: https://rapidapi.com/
  
- **Google API Key**: For search enhancement
  - Get from: https://console.cloud.google.com/
  - Also need Search Engine ID from: https://programmablesearchengine.google.com/

## 💻 Usage

### Basic Usage
```bash
python main.py
```

### Search Types
1. **Product Searches**
   - Direct product names
   - Product categories
   - Feature-based queries

2. **Smart Queries**
   - Natural language questions
   - Comparative queries
   - Technical specifications

3. **Non-Product Queries**
   - Recipe suggestions
   - General information
   - Technical advice

## 🔧 Development

### Project Structure
```
├── main.py                 # Application entry point
├── product_search_gui.py   # GUI implementation
├── batch_search.py         # Search processing
├── amazon_api_client.py    # Amazon API integration
├── google_search_client.py # Google Search integration
├── query_validator.py      # Query processing
├── data_store.py          # Data management
├── requirements.txt        # Dependencies
└── .env.template          # Environment template
```

### Adding New Features
1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests if applicable
5. Submit a pull request

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

### Guidelines
1. Follow Python PEP 8 style guide
2. Add documentation for new features
3. Maintain test coverage
4. Update README as needed

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments
- OpenAI for GPT API
- RapidAPI for Amazon Data API
- Google Custom Search API
- Qt framework (PySide6)
- All contributors and users

## 📞 Support
- Create an issue for bug reports
- Submit feature requests via issues
- Check existing issues before submitting new ones

## 🔒 Security
- Never commit API keys
- Use .env for sensitive data
- Regular security audits
- Prompt key rotation
