from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
THINGSBOARD_SERVER = os.getenv('THINGSBOARD_URL')
JWT_TOKEN = os.getenv('JWT_TOKEN')
PROVISION_KEY = os.getenv('PROVISION_KEY')
PROVISION_SECRET = os.getenv('PROVISION_SECRET')