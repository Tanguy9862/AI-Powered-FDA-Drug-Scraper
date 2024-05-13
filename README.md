# 🔄 New Drug Approvals Scraper

This Python package automates the scraping, cleaning, and classification of new drug approval data from [Drugs.com](https://www.drugs.com/newdrugs.html). Designed for robustness and versatility, it integrates data processing techniques with AI-driven classification, enabling enriched data analysis within dynamic environments like Dash applications.

## 🧹 Data Cleaning and Normalization
### 🧽 Cleaning Techniques

The scraper meticulously extracts and refines data, addressing variations in drug names, generics, and administration methods. Using regular expressions, the `extract_generic_and_admin` function isolates and sanitizes these components, ensuring data uniformity and precision.

### 🔧 Normalization

Company names undergo rigorous normalization to resolve inconsistencies in formatting and abbreviations. The `clean_company_name` function standardizes variations, reducing potential data duplicity from around 1000 to 700 distinct entries, which enhances data reliability for further analysis.

## 🏷️ Data Classification with AI

Utilizing LangChain and OpenAI's LLMs, the scraper enriches the extracted data by categorizing medications and their treatment categories. This process not only simplifies complex medical information but also facilitates insightful trend analysis across various disease treatments. The integration with LangChain allows dynamic interaction with data, applying logical rules to categorize drugs based on their detailed descriptions and intended uses.

## 📦 Package Structure and Versatility

The scraper is structured as a Python package, enabling it to function independently or as part of larger systems:

- `scraper.py`: Handles data collection logic.
- `classification.py`: Manages AI-driven data categorization.
- `utils.py`: Provides utility functions for data manipulation.
- `init.py`: Initializes the directory as a Python package for easy import.

## 🔄 Using the Scraper

The main function, `scrape_new_drug_approvals_data`, is designed for flexibility:

- **Standalone Execution:** Updates a local CSV file with the latest drug approvals.
- **Integration with Dash:** Returns a DataFrame directly, enabling real-time data refresh in Dash applications whenever invoked.

## 🌐 Example Integration

For a live example of how this scraper package is utilized within a Dash ecosystem to provide real-time updates on drug approvals, visit the [New Drug Approvals Dashboard repository](https://github.com/Tanguy9862/new-drug-approvals-dashboard).
