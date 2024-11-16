from tb_rest_client.rest_client_pe import RestClientPE
from tb_rest_client.rest import ApiException
from dotenv import load_dotenv
import json
import os

# Load environment variables
load_dotenv()
THINGSBOARD_SERVER = os.getenv('THINGSBOARD_URL')
# ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
PROVISION_KEY = os.getenv('PROVISION_KEY')
PROVISION_SECRET = os.getenv('PROVISION_SECRET')
JWT_TOKEN = os.getenv('JWT_TOKEN')

def get_rest_client():
    rest_client = RestClientPE(base_url=THINGSBOARD_SERVER)
    # Login to the server with JWT token
    rest_client.token_login(JWT_TOKEN)
    return rest_client

if __name__ == '__main__':
    # Create a REST client
    with get_rest_client() as rest_client:
        try:
            # Create a new device
            device = rest_client.save_device({
                "name": "ESP-WROOM-32",
                "type": "ESP32 MCU",
                "label": "WiFi-BT-BLE MCU",
                "additionalInfo": {
                    "description": "Test Device for the Project"
                }
            })
            print(f"Device created: {device}")

        except ApiException as e:
            body = json.loads(e.body.decode('utf-8'))
            print(f"Failed: {e.status}, Reason: {e.reason}, Message: {body.get('message')}")#, Response: {e.body}")
        finally:
            # Disconnect from the server
            rest_client.logout() if rest_client.logged_in else None