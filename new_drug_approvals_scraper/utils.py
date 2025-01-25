import re
import logging
import pandas as pd
from langchain_openai import ChatOpenAI
from html import unescape
from typing import Union
from .config import CONFIG


def get_most_recent_year(df: pd.DataFrame, date_column: str = 'Date of Approval') -> Union[int, bool]:
    """
    Returns the year of the most recent date in the specified column.

    Args:
        df (pd.DataFrame): DataFrame containing the data.
        date_column (str): Name of the column with date values.

    Returns:
        Union[int, bool]: The most recent year or False if no valid dates are found.
    """
    try:
        # Convert the column to datetime, handling invalid values
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        most_recent_date = df[date_column].max()
        if pd.isna(most_recent_date):
            logging.error(f"No valid dates found in column `{date_column}`.")
            return False
        return most_recent_date.year
    except Exception as e:
        logging.error(f"Error while processing column `{date_column}`: {e}")
        raise ValueError(f"Failed to get the most recent year from column `{date_column}`.")


def clean_mode_administration(mode: str) -> str:
    """
    Cleans the mode of administration string by removing any parts
    with 'formerly' and removing 'for' if it's the first word.

    Args:
        mode (str): The original mode of administration text.

    Returns:
        str: The cleaned mode of administration.
    """

    mode = re.sub(r'\s*-\s*formerly.*', '', mode)
    mode = re.sub(r'^for\s+', '', mode, flags=re.IGNORECASE)
    return mode.strip()


def extract_generic_and_admin(drug_tag: str) -> tuple:
    """
    Extracts the generic name and mode of administration from a drug tag string.

    Args:
        drug_tag (str): The string containing the drug information typically in an HTML-like format.

    Returns:
        tuple: A tuple containing the generic name and cleaned mode of administration,
               or (None, None) if no data is found.
    """

    # Try to capture nested parentheses and then text following until tag close or end of string
    match = re.search(r'\(((?:[^\(\)]|\([^\)]*\))*)\)\s*(.*)', unescape(drug_tag))

    if match:
        generic_name, mode_administration = match.group(1).strip(), match.group(2).strip()

        # Handle empty parentheses case
        if not generic_name:
            generic_name = None

        mode_administration = re.sub(r'<\/?\w+>', '', mode_administration).strip()

        return generic_name, clean_mode_administration(mode_administration)

    return None, None


def clean_company_name(company_name: str) -> str:
    """
    Cleans and standardizes the company name by replacing certain conjunctions,
    removing specified suffixes, and converting names to a standard abbreviation
    if applicable. This helps in maintaining consistency in company names across the dataset.


    Args:
        company_name (str): The original company name.

    Returns:
       str: The standardized and cleaned company name.
    """

    # Normalize the case, strip whitespace, and replace separators with 'and'
    company_name = company_name.lower().strip()
    company_name = re.sub(r'\s*(?:/|&|\+)\s*', ' and ', company_name)

    # List of suffixes to remove from the company name
    suffixes_to_remove = [
        r'\.', r'\,', r'\;', r'\binc\b', r'\bltd\b', r'\bglobal\b', r'\blimited\b',
        r'\bllc\b', r'\bcorp\b', r'\ba\/s\b', r'\bcorporation\b', r'\bs\.a\b',
        r'\bgmbh\b', r'\bag\b', r'\bplc\b', r'\band co\b', r'\band company\b',
        r'\bl\.p\b', r'& co', r'\bsa\b', r'\busa\b', r'\blp\b', r'\bus\b', r'\bincorporated\b',
        r'\bpharma\b', r'\blaboratories\b', r'\bindustries\b', r'\bcompany\b'
    ]

    # Remove special characters such as periods and commas
    company_name = re.sub(r'[.,]', '', company_name)

    for suffix in suffixes_to_remove:
        company_name = re.sub(suffix, "", company_name).strip()

    # Convert full names to standard abbreviations if applicable
    standard_names = {
        'glaxosmithkline': 'gsk'
    }
    company_name = standard_names.get(company_name, company_name)

    return company_name.title()


def initialize_model(api_key: str) -> ChatOpenAI:
    """
    Initialize and return a ChatOpenAI model configured with the specified API key.

    Args:
        api_key (str): The API key for accessing OpenAI services.

    Returns:
        ChatOpenAI: A ChatOpenAI object initialized with the specified model and API key.
    """
    return ChatOpenAI(temperature=0.0, model=CONFIG.LLM_MODEL, openai_api_key=api_key)

