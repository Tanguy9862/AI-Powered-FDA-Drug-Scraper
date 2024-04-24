import os

from dotenv import load_dotenv
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Configuration for drug and disease categories
DRUG_CATEGORIES = "Antibiotics, Antivirals, Antifungals, Antiparasitics, Antineoplastics, Anti-inflammatories, " \
                  "Analgesics, Antipsychotics, Antidepressants, Antidiabetics, Cardiovascular, Respiratory, " \
                  "Gastrointestinal, Neurological, Dermatological, Ophthalmological, Hormonal, Immunological, " \
                  "Anesthetics, Vaccines, Nutritional Supplements"

DISEASE_CATEGORIES = "Infectious Diseases, Autoimmune Diseases, Cardiovascular Diseases, Neurological Disorders, " \
                     "Cancers, Respiratory Diseases, Gastrointestinal Diseases, Endocrine Disorders, " \
                     "Genetic Disorders, Mental Health Disorders, Musculoskeletal Disorders, Hematological Disorders, " \
                     "Dermatological Conditions, Renal Disorders, Ophthalmological Disorders, Hepatic Disorders, " \
                     "Reproductive System Disorders, Nutritional Disorders, Developmental Disorders, Traumatic Injuries"

# Descriptions for classification
DRUG_DESCRIPTION = "Classify the drug based on its name, mode of administration, description, and indicated treatment " \
                   "into the following categories: {categories}. If the drug does not clearly fit into any of these " \
                   "categories, output 'Other'."
DISEASE_DESCRIPTION = "Classify the disease based on the drug name used, and indicated treatment into the following " \
                      "categories: {categories}. If the disease does not clearly fit into any of these categories, " \
                      "output 'Other'."

# Templates for classification
DRUG_CLASSIFICATION_TEMPLATE = """\
For the following drug details, classify the drug into the appropriate category:

Drug Name: {drug_name}
Mode of Administration: {mode_administration}
Description: {drug_description}
Indicated Treatment: {drug_treatment}

Categories: {categories}

{format_instructions}
"""

DISEASE_CLASSIFICATION_TEMPLATE = """\
For the following details, classify the disease into the appropriate category:

Drug Name: {drug_name}
Indicated Treatment: {drug_treatment}

Categories: {categories}

{format_instructions}
"""

# Initialize configuration for API access.
load_dotenv()
LLM_MODEL = "gpt-3.5-turbo"
API_KEY = os.getenv('OPENAI_API_KEY')
chat = ChatOpenAI(temperature=0.0, model=LLM_MODEL, openai_api_key=API_KEY)


def setup_classification_schema(description: str) -> ResponseSchema:
    """
    Creates and returns a response schema for classification.

    Args:
        description (str): Description of the item to be classified.

    Returns:
        ResponseSchema: Configured response schema.
    """
    return ResponseSchema(name="item_category", description=description)


def make_classification(categories: str, item_description: str, template: str, **kwargs) -> str:
    """
    Classifies an item using LangChain model based on provided details.

    Args:
        categories (str): Comma-separated list of possible categories.
        item_description (str): Description of the item for classification.
        template (str): Template for the classification request.
        **kwargs: Dynamic arguments used to fill in the template.

    Returns:
        str: Resulting category from the classification.
    """
    response_schema = setup_classification_schema(item_description)
    output_parser = StructuredOutputParser.from_response_schemas([response_schema])
    format_instructions = output_parser.get_format_instructions()

    prompt = ChatPromptTemplate.from_template(template=template)
    messages = prompt.format_messages(
        categories=categories,
        format_instructions=format_instructions,
        **kwargs
    )

    response = chat.invoke(messages)
    output_dict = output_parser.parse(response.content)
    return output_dict['item_category']
