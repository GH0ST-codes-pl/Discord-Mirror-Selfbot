import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('SECRET_TOKEN')
SOURCE_ID = int(os.getenv('SOURCE_ID', 0))
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
REPORT_WEBHOOK_URL = os.getenv('REPORT_WEBHOOK_URL')
