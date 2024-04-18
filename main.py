import logging
import os

import requests
import pandas as pd
from datetime import datetime
from time import sleep
from bs4 import BeautifulSoup, NavigableString

# Regarder si j'ai déjà des données existantes
csv_file = 'new_drug_approvals.csv'
file_exists = os.path.isfile(csv_file)

if file_exists:
    # RECUPERER LA DERNIERE ANNEE
    pass
else:
    last_date = None

CURRENT_YEAR, END_YEAR = int(datetime.utcnow().year), 2002
headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:108.0) Gecko/20100101 Firefox/108.0"}
# Commencer à l'année actuelle


# TODO :
# Pour les noms génériques, ne chopper seulement que ce qui est entre parenthèses, pas le reste
# En fait les parenthèses c'est le générique et la suite c'est le mode d'adm
# Donc faire un split pour aussi récupérer le mode d'adm

i = 0
CURRENT_YEAR = 2023

while CURRENT_YEAR >= END_YEAR:

    # if i <= 15:
    response = requests.get(f'https://www.drugs.com/newdrugs-archive/{CURRENT_YEAR}.html', headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    # print(soup)

    # Retrieve all drug blocks contained within the main 'ddc-media-list' div
    all_drugs = soup.select_one('div.ddc-media-list').find_all('div', class_='ddc-media')
    for drug in reversed(all_drugs):
        new_data = dict()
        print('************')
        # print(drug)

        drug_tag = drug.find('h3', class_='ddc-media-title')
        new_data['drug_name'] = drug_tag.find('a').text if drug_tag.find('a') else drug_tag.text.split('(')[0]
        new_data['drug_generic_name'] = ''.join([t for t in drug_tag if isinstance(t, NavigableString)]).strip()

        print(drug_tag.find('a').text if drug_tag.find('a') else drug_tag.text)

        metadata_headers = ['Date of Approval:', 'Company:', 'Treatment for:']
        for header in metadata_headers:
            header_tag = drug.find('b', string=header)
            if header_tag:
                value = header_tag.next_sibling.strip()
                print(value)
                new_data[header.split(':')[0]] = value

        drug_df = pd.DataFrame([new_data])
        drug_df.to_csv(csv_file, mode='a', header=not file_exists, index=False)
        file_exists = True

        # print(new_data)

        # break

    CURRENT_YEAR -= 1
        # i += 1

    # break
    # Boucle pour chaque médicament
    # tmp_data
    # Scraper info générale
    # On scrape la date, si c'est la même que la dernière date du csv existant alors on break
    # Récupérer url de la fiche du médicament
    # Appel de l'agent LLM pour récupérer info secondaires
    # Enregistrer les nouvelles données dans tmp_data
    # Si tmp_data représente 10 % == 0 alors enregistre dans le csv (= toutes les 10 entrées)
    # Clear tmp_data

# retour début de boucle
# Une fois que j'ai terminé la boucle alors année - 1
