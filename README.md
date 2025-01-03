# Amazon Product Search

An intelligent product search application that combines Amazon's product data with AI-powered query understanding.

## Features

- Smart query understanding using OpenAI and Google Search
- Real-time Amazon product search
- Product comparison tools
- Search history tracking
- Alternative product suggestions
- Non-product query handling (recipes, medical info, etc.)

## Requirements

- Python 3.8+
- PySide6 for GUI
- OpenAI API key
- RapidAPI key (for Amazon Data API)
- Google API key and Custom Search Engine ID

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/amazon-product-search.git
cd amazon-product-search
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   - Copy `.env.template` to a new file named `.env`
   - Fill in your API keys in the `.env` file:
```
# Get your OpenAI API key from: https://platform.openai.com/account/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Get your RapidAPI key from: https://rapidapi.com/
RAPIDAPI_KEY=your_rapidapi_key_here

# Get Google API credentials from: https://console.cloud.google.com/
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_ENGINE_ID=your_search_engine_id_here
```

> ⚠️ **Important**: Never commit your `.env` file to version control. It contains sensitive API keys.

## Usage

Run the main application:
```bash
python main.py
```

### Features:
1. **Product Search**
   - Enter product queries
   - View detailed product information
   - Compare multiple products

2. **Smart Query Understanding**
   - Handles non-product queries
   - Provides relevant information
   - Suggests related products

3. **History and Tracking**
   - Save search history
   - Track product comparisons
   - View alternative suggestions

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for GPT API
- RapidAPI for Amazon Data API
- Google Custom Search API
- PySide6 for the GUI framework
