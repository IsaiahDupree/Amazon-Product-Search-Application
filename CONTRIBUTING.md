# Contributing to Amazon Product Search Application

First off, thank you for considering contributing to the Amazon Product Search Application! It's people like you that make this tool better for everyone.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots if possible

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Include screenshots and animated GIFs in your pull request whenever possible
* Follow the Python styleguides
* Include thoughtfully-worded, well-structured tests
* Document new code based on the Documentation Styleguide
* End all files with a newline

## Styleguides

### Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line

### Python Styleguide

* Follow PEP 8
* Use consistent naming conventions
* Include docstrings for all classes and methods
* Keep functions focused and small
* Use type hints where possible

### Documentation Styleguide

* Use Markdown
* Reference functions and classes with backticks
* Include code examples where relevant
* Keep line length to 80 characters
* Include section headers

## Development Process

1. Fork the repo
2. Create a new branch from `main`
3. Make your changes
4. Run tests
5. Push to your fork
6. Submit a Pull Request

### Setting Up Development Environment

```bash
# Clone your fork
git clone https://github.com/your-username/Amazon-Product-Search-Application.git
cd Amazon-Product-Search-Application

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up pre-commit hooks
pre-commit install
```

### Running Tests

```bash
python -m pytest
```

### Code Quality Checks

Before submitting:
1. Run pylint
2. Run black formatter
3. Check type hints with mypy
4. Ensure all tests pass

## Project Structure

Understanding the project structure is key to making contributions:

```
├── main.py                 # Application entry
├── product_search_gui.py   # GUI implementation
├── batch_search.py         # Search processing
├── amazon_api_client.py    # Amazon API integration
├── google_search_client.py # Google Search integration
├── query_validator.py      # Query processing
├── data_store.py          # Data management
├── tests/                  # Test files
│   ├── test_search.py
│   ├── test_api.py
│   └── test_gui.py
└── docs/                   # Documentation
```

## Questions?

Feel free to contact the project maintainers if you have any questions. We're here to help!
