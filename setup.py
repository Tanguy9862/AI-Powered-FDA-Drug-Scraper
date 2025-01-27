from setuptools import setup, find_packages

setup(
    name='new_drug_approvals_scraper',
    version='0.1.1',
    author='SUROWIEC Tanguy',
    description='A comprehensive package for scraping and processing new drug approval data.',
    url='https://github.com/Tanguy9862/scraper-new-drug-approvals',
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4',
        'requests',
        'tqdm',
        'langchain',
        'openai',
        'pandas',
        'python-dotenv',
        'langchain-openai',
        'boto3',
        'google-cloud-storage'
    ]
)
