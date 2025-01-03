# SPECIFICATION: Amazon API + LLM (Python)

## 1. Overview

This project will:

- **Query** the Amazon API to **search** products (e.g., searching by keyword, category).
- **Retrieve** product details, including price, title, rating, etc.
- **Use** a Large Language Model (ChatGPT or other) to:
  - Summarize or compare products.
  - Generate compatibility or comparison tables if multiple products are provided.

**Recommended language**: **Python**  
Reasoning: Python has robust HTTP and JSON libraries (`requests`), many popular ML/LLM libraries (`openai`), and strong data handling (`pandas` optional).

---

## 2. Core Features & Flow

### 2.1. Searching on Amazon

1. **User Input**: A keyword or phrase to search.  
2. **API Call** (example: RapidAPI's `real-time-amazon-data`):
   - `GET /search` endpoint with query params like `query=phone`, `page=1`, etc.  
   - Returns a JSON with a list of products.
3. **Data Extraction**:
   - **asin**  
   - **title**  
   - **price**  
   - **rating**  
   - **url**  
   - **images**  
   - Additional fields as needed (brand, category, etc.).

### 2.2. Product Details & Summaries

1. **Product Details**: Use the Amazon API's "Product Details" endpoint to fetch more info by `asin`.  
2. **LLM Summaries**:
   - Pass product data to ChatGPT or another LLM with a prompt such as:  
     > "Summarize these product details in a concise paragraph."  
   - Example library call in Python:  
     ```python
     import openai

     openai.api_key = "YOUR_OPENAI_KEY"

     def summarize_product(product_info):
         prompt = f"Summarize these specs: {product_info}"
         response = openai.Completion.create(
             model="text-davinci-003",
             prompt=prompt,
             max_tokens=150
         )
         return response.choices[0].text.strip()
     ```

### 2.3. Comparison & Compatibility Table

If the user inputs multiple ASINs or a list of product links:
1. **Fetch** details for each product via the Amazon API.  
2. **Construct** a data structure (e.g., a list of dicts) capturing attributes (price, rating, brand, features).  
3. **Generate** a summary or table:
   - Option A: Manual code to create an HTML or Markdown table.  
   - Option B: Pass the product attributes to the LLM with a prompt like:
     > "Create a comparison table of these products with columns for Price, Rating, Brand, and Key Features. Return valid Markdown."  

   - Use the LLM's output in your UI or text-based interface.

---

## 3. Key Variables & Parameters

Below are typical parameters and environment variables you'll need:

1. **RAPIDAPI_KEY** (stored in `.env` or secrets):
   - Used in `X-RapidAPI-Key` header for the Amazon API calls.

2. **OPENAI_API_KEY** (also in `.env`):
   - For ChatGPT or another LLM, used in the `Authorization: Bearer` or `openai.api_key`.

3. **Amazon API Endpoints** (RapidAPI "real-time-amazon-data" example):
   - **Search**: `GET https://real-time-amazon-data.p.rapidapi.com/search`
     - Query params: `query`, `country`, `page`, `sort_by`, etc.
   - **Product Details**: `GET https://real-time-amazon-data.p.rapidapi.com/product-details`
     - Query param: `asin` (plus `country`).

4. **LLM Model**:
   - e.g., `"gpt-3.5-turbo"` or `"gpt-4"` or your model of choice.
   - Config: `temperature`, `max_tokens`, `top_p`, etc.

5. **Comparison Logic**:
   - Fields to compare: `price`, `rating`, `brand`, `features`, etc.
   - If building your own table code, specify columns, e.g., `[title, brand, price, rating, top_feature, ...]`.

6. **Prompts**:
   - Summaries: `"Summarize the key features and pros/cons."`
   - Table creation: `"Generate a side-by-side Markdown table with columns: Brand, Price, Rating, Key Feature."`

---

## 4. Project Structure (Python Example)

```
my-amazon-llm/
│
├── .env                        # Contains RAPIDAPI_KEY, OPENAI_API_KEY
├── requirements.txt            # requests, openai, python-dotenv, etc.
├── main.py                     # Entry point
├── amazon_client.py            # Functions for calling Amazon API
├── llm_client.py               # Functions for OpenAI calls
├── data_processing.py          # Compare, filter, sort logic
└── README.md
```

### 4.1. `requirements.txt`

```plaintext
requests
python-dotenv
openai
pandas    # optional if you want DataFrame-based comparisons
```

### 4.2. `amazon_client.py`

```python
import os
import requests

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

def search_amazon_products(query, page=1, country="US"):
    url = "https://real-time-amazon-data.p.rapidapi.com/search"
    headers = {
       "X-RapidAPI-Key": RAPIDAPI_KEY,
       "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }
    params = {
       "query": query,
       "page": page,
       "country": country,
       # add other sort/filter params as needed
    }
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()

def get_product_details(asin, country="US"):
    url = "https://real-time-amazon-data.p.rapidapi.com/product-details"
    headers = {
       "X-RapidAPI-Key": RAPIDAPI_KEY,
       "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }
    params = {
       "asin": asin,
       "country": country
    }
    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()
```

### 4.3. `llm_client.py`

```python
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_product(product_data):
    prompt = (
      "Please summarize the following product:\n\n"
      f"{product_data}\n\n"
      "Focus on key features and pros/cons."
    )
    resp = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=200,
        temperature=0.7
    )
    return resp.choices[0].text.strip()

def generate_comparison_table(products):
    # Construct a textual list or JSON of product attributes
    product_text = "\n".join(
      f"- {p['title']} (Brand: {p.get('brand')}): Price={p.get('price')} | Rating={p.get('rating')}"
      for p in products
    )
    prompt = (
      "Generate a Markdown comparison table for these products:\n"
      f"{product_text}\n\n"
      "Columns: Title, Brand, Price, Rating, Key Feature. Keep it short."
    )
    resp = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=300,
        temperature=0
    )
    return resp.choices[0].text.strip()
```

### 4.4. `main.py`

```python
from amazon_client import search_amazon_products, get_product_details
from llm_client import summarize_product, generate_comparison_table

def main():
    # 1. Search
    query = "smartphone"
    search_results = search_amazon_products(query)
    products = search_results.get("data", {}).get("products", [])
    print(f"Found {len(products)} products for '{query}'.")

    # 2. Summarize first product
    if products:
        asin = products[0]["asin"]
        details = get_product_details(asin)
        summary = summarize_product(details)
        print("Summary of first product:")
        print(summary)

    # 3. Compare multiple ASINs
    asin_list = ["B0XXXXXXX", "B0YYYYYYY", ...]  # example
    product_info_list = []
    for a in asin_list:
        det = get_product_details(a)
        # extract fields to a dict
        product_info_list.append({
            "title": det["data"]["product_title"],
            "brand": det["data"].get("brand"),
            "price": det["data"].get("product_price"),
            "rating": det["data"].get("product_star_rating"),
            # etc...
        })

    table = generate_comparison_table(product_info_list)
    print("Comparison Table:")
    print(table)

if __name__ == "__main__":
    main()
```

---

## 5. Deployment & Security

1. **Store Secrets** in `.env`:
   ```
   RAPIDAPI_KEY=...
   OPENAI_API_KEY=...
   ```
2. **Logging** & error handling: Use `logging` or other frameworks for production.
3. **Rate Limits**: The "real-time-amazon-data" plan may have usage constraints. Monitor carefully.

---

## 6. Potential Enhancements

- **Database** for caching product data and not re-calling the API.  
- **Front-end** in React/Vue to display results.  
- **Advanced Summaries** or "Buying Guides" using GPT-4.  
- **Evals** or tests to ensure LLM quality.  

---

## 7. Conclusion

With this reference, a developer can:

1. **Install** dependencies (`pip install -r requirements.txt`).  
2. **Configure** environment variables.  
3. **Run** `main.py` to see searching, detail fetching, summarizing, and generating a comparison table.  
4. **Extend** as needed for UI, advanced features, or additional LLM-based functionalities.

Happy coding!
