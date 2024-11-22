from tb_rest_client.rest_client_pe import RestClientPE, Device
from tb_rest_client.rest import ApiException
import json
from app.config import THINGSBOARD_SERVER, BRAM
import requests

def get_rest_client(username, password):
    tokens = authenticate(username, password)
    rest_client = RestClientPE(base_url=THINGSBOARD_SERVER)
    # Login to the server with JWT token
    rest_client.token_login(tokens['token'])
    rest_client.token_info = tokens  # Update token_info with the tokens value
    return rest_client

def get_user_tb(username, rest_client):
    user_page = rest_client.get_user_users(1, 1, username)
    if user_page.total_elements != 0:
        page = 1
        page_size = 1
        while True:
            user_page = rest_client.get_user_users(page, page_size)
            user = user_page.data[0] if user_page.data else None
            if user and user.email == username:
                return user
            if not user_page.has_next:
                break
            page += 1
    return None

def authenticate(username, password):
    url = 'https://thingsboard.cloud/api/auth/login'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    data = {
        'username': username,
        'password': password
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()  # Return the token object directly
    else:
        raise Exception(f"Authentication failed: {response.json()}")

if __name__ == '__main__':
    # Example usage
    tokens = authenticate('osura.bramwel@students.jkuat.ac.ke', 'Bramwel1!')
    access_token = tokens['token']
    refresh_token = tokens['refreshToken']

    # Create a REST client
    with get_rest_client(BRAM['email'], BRAM['password']) as rest_client:
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
            Device()
            rest_client.token_info.update()
            print(f"Device created: {device}")

        except ApiException as e:
            body = json.loads(e.body.decode('utf-8'))
            print(f"Failed: {e.status}, Reason: {e.reason}, Message: {body.get('message')}")#, Response: {e.body}")
        finally:
            # Disconnect from the server
            rest_client.logout() if rest_client.logged_in else None