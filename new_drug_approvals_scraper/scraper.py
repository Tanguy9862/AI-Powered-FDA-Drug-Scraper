import logging
import os
from dotenv import load_dotenv
from typing import Optional

from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import requests
from tqdm import tqdm

from .config import CONFIG, LocalConfig, AWSConfig, GCPConfig
from .load_data import (
    load_existing_data,
    export_data_to_local,
    export_data_to_s3,
    export_data_to_cloud_storage
)

from new_drug_approvals_scraper.utils import (
    initialize_model,
    extract_generic_and_admin,
    clean_company_name
)

from new_drug_approvals_scraper.classification import (
    make_classification,
    DRUG_CATEGORIES,
    DRUG_DESCRIPTION,
    DRUG_CLASSIFICATION_TEMPLATE,
    DISEASE_CATEGORIES,
    DISEASE_DESCRIPTION,
    DISEASE_CLASSIFICATION_TEMPLATE
)

# Initialize constants: date format, and browser headers
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def scrape_new_drug_approvals_data(openai_api_key: Optional[str] = None) -> None:
    """
    Scrapes drug approval data from Drugs.com and updates a local or cloud-hosted dataset.

    This function scrapes drug approvals data year by year from Drugs.com. It is designed to:
    - Check if a drug has already been scraped (based on its name) to avoid re-scraping duplicate data.
    - Export the resulting dataset to a local file, AWS S3, or Google Cloud Storage based on the configuration.

    **Workflow**:
    1. Loads the existing dataset (if any) to check for already scraped drugs.
    2. Iterates over years, starting from the current year and going backward, scraping new approvals.
    3. For each drug:
        - Extracts key metadata: name, generic name, mode of administration, approval date, company, etc.
        - Classifies the drug and its corresponding disease using a language model (OpenAI API).
    4. Updates the dataset and exports it to the configured storage.

    Args:
        openai_api_key (Optional[str]): The OpenAI API key used for classification. If not provided,
                                        the function attempts to load it from environment variables.

    Raises:
        ValueError: If the OpenAI API key is not provided and cannot be loaded from the environment.
        RuntimeError: If the storage configuration (`CONFIG`) is invalid.

    Returns:
        None: All data is either exported to a csv file or stored in the cloud.
    """
    # Initialize the language model with API key
    if not openai_api_key:
        load_dotenv()
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError('OpenAI API key not found. Please provide it as an argument or set it as an environment variable.')

    chat = initialize_model(openai_api_key)

    # Scraping process initialization
    df_initial, most_recent_year = load_existing_data() or (pd.DataFrame(), None)
    current_year, end_year = int(datetime.utcnow().year), (most_recent_year or CONFIG.BASE_YEAR)

    while current_year >= end_year:
        logging.info(f'[{current_year}] Scraping new drug approvals')
        response = requests.get(f'{CONFIG.BASE_URL}/{current_year}.html', headers=CONFIG.HEADERS)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Retrieve all drug blocks contained within the main 'ddc-media-list' div
            all_drugs = soup.select_one('div.ddc-media-list').find_all('div', class_='ddc-media')

            # for drug in tqdm(reversed(all_drugs)):
            for drug in tqdm(all_drugs):
                new_data = dict()

                # Get the content of the parent div from the current drug
                drug_tag = drug.find('h3', class_='ddc-media-title')

                # Get the drug name
                drug_name_to_check = drug_tag.find('a').text.strip() if drug_tag.find('a') else drug_tag.text.split('(')[0].strip()
                logging.info(f"[{current_year}] Processing drug: {drug_name_to_check} [...]")

                # Check if the drug name has already been scraped
                if not df_initial.empty:
                    has_been_scraped = df_initial.query('drug_name == @drug_name_to_check')
                    if not has_been_scraped.empty:
                        logging.info(f"[{current_year}]  Skipping '{drug_name_to_check}' as it has already been scraped.")
                        continue

                # Add the drug name to the dict
                new_data['drug_name'] = drug_name_to_check

                # Get the generic name and the mode of administration
                generic_name, mode_administration = extract_generic_and_admin(str(drug_tag))
                new_data['drug_generic_name'] = generic_name
                new_data['mode_administration'] = mode_administration

                # Get the description
                subtitle_tag = drug.find('p', class_='drug-subtitle')
                description_tag = subtitle_tag.find_next_sibling('p', class_=False)
                description_text = description_tag.get_text(strip=True) if description_tag else ''
                description_clean = description_text.replace(';', '').replace('\t', ' ')
                new_data['description'] = description_clean

                # Iterate through headers to extract key data from <b> tags, which uniquely contain
                # the metadata like approval date, company name, and treatment information
                for header in ['Date of Approval:', 'Company:', 'Treatment for:']:
                    header_tag = drug.find('b', string=header)

                    if header_tag:
                        # Clean the value by replacing semicolons with commas for 'Treatment for:', otherwise just strip
                        # whitespace
                        value = header_tag.next_sibling.strip().replace(';', ',') if header == 'Treatment for:' else header_tag.next_sibling.strip()
                        new_data[header.split(':')[0]] = value if header != 'Company:' else clean_company_name(value)

                # Perform drug classification
                new_data['drug_type'] = make_classification(
                    categories=DRUG_CATEGORIES,
                    item_description=DRUG_DESCRIPTION,
                    template=DRUG_CLASSIFICATION_TEMPLATE,
                    chat=chat,
                    drug_name=new_data.get('drug_name', None),
                    mode_administration=new_data.get('mode_administration', None),
                    drug_description=new_data.get('description', None),
                    drug_treatment=new_data.get('Treatment for', None),
                )

                # Perform disease classification
                new_data['disease_type'] = make_classification(
                    categories=DISEASE_CATEGORIES,
                    item_description=DISEASE_DESCRIPTION,
                    chat=chat,
                    template=DISEASE_CLASSIFICATION_TEMPLATE,
                    drug_name=new_data.get('drug_name', None),
                    drug_treatment=new_data.get('Treatment for', None)
                )

                # Append new scraped data to the existing CSV
                new_drug_df = pd.DataFrame([new_data])
                new_drug_df['Date of Approval'] = pd.to_datetime(new_drug_df['Date of Approval'], format=CONFIG.DATE_FORMAT)
                df_initial = pd.concat([new_drug_df, df_initial], ignore_index=True)

            current_year -= 1

        else:
            logging.error(
                f"[{current_year}] Failed to fetch data. HTTP status code: {response.status_code}. URL: {CONFIG.BASE_URL}/{current_year}.html")

    if isinstance(CONFIG, LocalConfig):
        export_data_to_local(df_initial)
    elif isinstance(CONFIG, AWSConfig):
        export_data_to_s3(df_initial)
    elif isinstance(CONFIG, GCPConfig):
        export_data_to_cloud_storage(df_initial)
    else:
        raise RuntimeError(
            f"Invalid CONFIG detected. CONFIG must be an instance of either LocalConfig, AWSConfig, or GCPConfig. "
            f"Current CONFIG: {type(CONFIG).__name__}"
        )
