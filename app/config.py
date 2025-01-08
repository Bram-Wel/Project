from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()
THINGSBOARD_SERVER = os.getenv('THINGSBOARD_URL')
BRAM = json.loads(os.getenv('BRAM'))[0]
PROVISION_KEY = os.getenv('PROVISION_KEY')
PROVISION_SECRET = os.getenv('PROVISION_SECRET')