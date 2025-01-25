from pathlib import Path
from dotenv import load_dotenv
import os

env_path = Path.cwd() / ".env"
load_dotenv(dotenv_path=env_path)
ENV = os.getenv("ENV", "local")


# Only for if you want to access to your Cloud Storage from Local
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'spacexploration-gcp-bucket-access.json' or None


class BaseConfig:
    SCRIPT_NAME = 'new_drug_approvals_scraper'
    DATE_FORMAT = '%B %d, %Y'
    BASE_YEAR = 2002
    LLM_MODEL = 'gpt-4o-mini'
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Mobile Safari/537.36", }
    BASE_URL = 'https://www.drugs.com/newdrugs-archive'
    DATA_EXPORT_FILENAME = "new_drug_approvals.csv"


class LocalConfig(BaseConfig):
    DATA_DIR_NAME = 'data'


class AWSConfig(BaseConfig):
    BUCKET_NAME = "new-drug-approvals-s3"


class GCPConfig(BaseConfig):
    BUCKET_NAME = 'new-drug-approvals-bucket'


def get_config():
    if ENV == "local":
        return LocalConfig()
    elif ENV == 'aws':
        return AWSConfig()
    elif ENV == 'gcp':
        return GCPConfig()
    return LocalConfig()


CONFIG = get_config()
