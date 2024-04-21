import logging
import os

from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import requests
from tqdm import tqdm

from utils import extract_generic_and_admin, clean_company_name

# Initialize constants: current and end years for scraping, date format, and browser headers
CURRENT_YEAR, END_YEAR = int(datetime.utcnow().year), 2002
DATE_FORMAT = '%B %d, %Y'
headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0"}
logging.basicConfig(level=logging.INFO)

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

# Flag to determine when to stop scraping based on new data availability
has_to_stop = False

while CURRENT_YEAR >= END_YEAR:

    if not has_to_stop:

        logging.info(f'Scraping new drug approvals for {CURRENT_YEAR}')
        response = requests.get(f'https://www.drugs.com/newdrugs-archive/{CURRENT_YEAR}.html', headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Retrieve all drug blocks contained within the main 'ddc-media-list' div
        all_drugs = soup.select_one('div.ddc-media-list').find_all('div', class_='ddc-media')
        for drug in tqdm(reversed(all_drugs)):

            new_data = dict()

            # Get the content of the parent div from the current drug
            drug_tag = drug.find('h3', class_='ddc-media-title')

            # Get the drug name
            drug_name = drug_tag.find('a').text if drug_tag.find('a') else drug_tag.text.split('(')[0]
            new_data['drug_name'] = drug_name

            # Get the generic name and the mode of administration
            generic_name, mode_administration = extract_generic_and_admin(str(drug_tag))
            new_data['drug_generic_name'] = generic_name
            new_data['mode_administration'] = mode_administration

            # Get the description
            subtitle_tag = drug.find('p', class_='drug-subtitle')
            description_tag = subtitle_tag.find_next_sibling('p', class_=False)
            description = (description_tag or None) and description_tag.get_text(strip=True)
            new_data["description"] = description

            # Iterate through headers to extract key data from <b> tags, which uniquely contain
            # the metadata like approval date, company name, and treatment information
            metadata_headers = ['Date of Approval:', 'Company:', 'Treatment for:']
            for header in metadata_headers:
                header_tag = drug.find('b', string=header)
                if header_tag:
                    value = header_tag.next_sibling.strip()

                    # Check if the current drug and its approval date match the most recently scraped drug and date:
                    if header == 'Date of Approval:':
                        date_formatted = datetime.strptime(value, DATE_FORMAT)

                        # If the current drug and its approval date match the most recently recorded drug and date,
                        # it indicates there are no new updates to scrape, and the process should stop.
                        if drug_name == most_recent_drug and date_formatted == most_recent_date:
                            logging.info(f'{most_recent_drug} was the last drug scraped previously.\n'
                                         f'Scraping has now been completed.')
                            has_to_stop = True
                            break

                    # Otherwise, add scraped data to `new data`
                    new_data[header.split(':')[0]] = value if header != 'Company:' else clean_company_name(value)

            if has_to_stop:
                break

            # Append new scraped data to the existing CSV
            drug_df = pd.DataFrame([new_data])
            drug_df['Date of Approval'] = pd.to_datetime(drug_df['Date of Approval'], format=DATE_FORMAT)
            drug_df.to_csv(csv_file, mode='a', header=not file_exists, index=False)
            if not file_exists:
                file_exists = True

        CURRENT_YEAR -= 1

    else:
        break
