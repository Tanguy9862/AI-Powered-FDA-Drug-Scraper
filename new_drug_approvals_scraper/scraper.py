import logging
import os

from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import requests
from tqdm import tqdm

from new_drug_approvals_scraper.utils import extract_generic_and_admin, clean_company_name
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
DATE_FORMAT = '%B %d, %Y'
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0"}
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def scrape_new_drug_approvals_data():

    # Check for existing CSV file to determine if we need to update or initialize data
    csv_file = 'new_drug_approvals.csv'
    file_exists = os.path.isfile(csv_file)

    if file_exists:
        df = pd.read_csv(csv_file)
        df['Date of Approval'] = pd.to_datetime(df['Date of Approval'], format='%Y-%m-%d', errors='coerce')
        df_sorted = df.sort_values(by='Date of Approval', ascending=False)
        most_recent = df_sorted.iloc[0]
        most_recent_date, most_recent_drug = most_recent['Date of Approval'], most_recent['drug_name']
    else:
        most_recent_date, most_recent_drug = None, None

    # Initialize current_year and end_year
    current_year, end_year = int(datetime.utcnow().year), 2002

    # Flag to determine when to stop scraping based on new data availability
    has_to_stop = False

    while current_year >= end_year:

        if not has_to_stop:

            logging.info(f'[YEAR] Scraping new drug approvals for {current_year}')
            response = requests.get(f'https://www.drugs.com/newdrugs-archive/{current_year}.html', headers=HEADERS)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Retrieve all drug blocks contained within the main 'ddc-media-list' div
            all_drugs = soup.select_one('div.ddc-media-list').find_all('div', class_='ddc-media')
            for drug in tqdm(reversed(all_drugs)):

                new_data = dict()

                # Get the content of the parent div from the current drug
                drug_tag = drug.find('h3', class_='ddc-media-title')

                # Get the drug name
                new_data['drug_name'] = drug_tag.find('a').text if drug_tag.find('a') else drug_tag.text.split('(')[0]
                logging.info(f'[DRUG] Scraping data for {new_data.get("drug_name", None)}')

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

                        # Check if the current drug and its approval date match the most recently scraped drug and date:
                        if header == 'Date of Approval:':
                            date_formatted = datetime.strptime(value, DATE_FORMAT)

                            # If the current drug and its approval date match the most recently recorded drug and date,
                            # it indicates there are no new updates to scrape, and the process should stop.
                            if new_data['drug_name'] == most_recent_drug and date_formatted == most_recent_date:
                                logging.info(f'{most_recent_drug} was the last drug scraped previously.\n'
                                             f'Scraping has now been completed.')
                                has_to_stop = True
                                break

                        # Otherwise, add scraped data to `new data`
                        new_data[header.split(':')[0]] = value if header != 'Company:' else clean_company_name(value)

                if has_to_stop:
                    break

                # Perform drug classification
                new_data['drug_type'] = make_classification(
                    categories=DRUG_CATEGORIES,
                    item_description=DRUG_DESCRIPTION,
                    template=DRUG_CLASSIFICATION_TEMPLATE,
                    drug_name=new_data.get('drug_name', None),
                    mode_administration=new_data.get('mode_administration', None),
                    drug_description=new_data.get('description', None),
                    drug_treatment=new_data.get('Treatment for', None),
                )

                # Perform disease classification
                new_data['disease_type'] = make_classification(
                    categories=DISEASE_CATEGORIES,
                    item_description=DISEASE_DESCRIPTION,
                    template=DISEASE_CLASSIFICATION_TEMPLATE,
                    drug_name=new_data.get('drug_name', None),
                    drug_treatment=new_data.get('Treatment for', None)
                )

                # Append new scraped data to the existing CSV
                drug_df = pd.DataFrame([new_data])
                drug_df['Date of Approval'] = pd.to_datetime(drug_df['Date of Approval'], format=DATE_FORMAT)
                drug_df.to_csv(csv_file, mode='a', header=not file_exists, index=False)
                if not file_exists:
                    file_exists = True

            current_year -= 1

        else:
            break

    return logging.info('Drug Approvals Data Updated!')
