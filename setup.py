from setuptools import setup, find_packages

setup(
    name='new_drug_approvals_scraper',
    version='0.1.1',
    author='SUROWIEC Tanguy',
    description='A comprehensive package for scraping and processing new drug approval data.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Tanguy9862/scraper-new-drug-approvals',
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4==4.12.3',
        'requests~=2.31.0',
        'tqdm~=4.66.2',
        'langchain~=0.1.16',
        'openai',
        'pandas',
        'python-dotenv',
        'langchain-openai',
        'boto3',
        'google-cloud-storage'
    ]
)
