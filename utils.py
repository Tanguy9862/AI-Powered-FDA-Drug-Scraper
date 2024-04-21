import re


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
    match = re.search(r'\(((?:[^\(\)]|\([^\)]*\))*)\)\s*(.*)', drug_tag)

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
    Cleans the company name by removing specified suffixes and special characters.

    Args:
        company_name (str): The original company name.

    Returns:
        str: The cleaned company name.
    """

    # List of suffixes to remove from the company name
    suffixes_to_remove = [
        r'\.', r'\,', r'\binc\b', r'\bltd\b', r'\bglobal\b', r'\blimited\b',
        r'\bllc\b', r'\bcorp\b', r'\ba\/s\b', r'\bcorporation\b', r'\bs\.a\b',
        r'\bgmbh\b', r'\bag\b', r'\bplc\b', r'\band co\b', r'\band company\b',
        r'\bl\.p\b', r'& co', r'\bsa\b', r'\busa\b', r'\blp\b', r'\bus\b', r'\bincorporated\b',
        r'\bpharma\b', r'\blaboratories\b'
    ]

    company_name = company_name.lower()

    # Remove special characters such as periods and commas
    company_name = re.sub(r'[.,]', '', company_name)

    for suffix in suffixes_to_remove:
        company_name = re.sub(suffix, "", company_name).strip()

    return company_name




