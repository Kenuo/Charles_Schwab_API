import base64
import requests
import webbrowser
import time
import os
from dotenv import load_dotenv

load_dotenv()

#Write the access token and refresh token to a file.
def write_in_file(access_token, refresh_token):
    file_path = os.getenv("FILE_PATH")
    with open(file_path, "w") as f:
        f.write(f"{access_token}\n{refresh_token}")

#Retrieve access and refresh tokens using authorization code.
def retrieve_tokens(app_key, encoded_credentials, callback_url):
    auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?client_id={app_key}&redirect_uri={callback_url}"

    # Open the authorization URL for user sign-in on Charles Schwab
    webbrowser.open(auth_url)

    returned_url = input("----------------------\nEnter copied URL:\n----------------------\n")
    auth_code = f"{returned_url[returned_url.index('code=') + 5: returned_url.index('%40')]}@"

    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": callback_url
    }

    response = requests.post("https://api.schwabapi.com/v1/oauth/token", data=data, headers=headers)
    response_json = response.json()

    return response_json.get("access_token"), response_json.get("refresh_token")

def refresh_access_token(refresh_token, encoded_credentials):
    """Refresh the access token using the refresh token."""
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    response = requests.post("https://api.schwabapi.com/v1/oauth/token", data=data, headers=headers)
    response_json = response.json()

    access_token = response_json.get("access_token")
    new_refresh_token = response_json.get("refresh_token")

    if access_token:
        write_in_file(access_token, new_refresh_token)
        print("Tokens refreshed successfully.")

if __name__ == '__main__':
    # Application setup
    callback_url = "https://127.0.0.1"
    app_key = os.getenv("APP_KEY")
    secret_code = os.getenv("SECRET_CODE")

    # Encode credentials
    credentials = f"{app_key}:{secret_code}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    # Retrieve and store initial tokens
    access_token, refresh_token = retrieve_tokens(app_key, encoded_credentials, callback_url)
    write_in_file(access_token, refresh_token)

    # Refresh tokens every 29 minutes
    while True:
        time.sleep(1740)  # Wait for 29 minutes
        refresh_access_token(refresh_token, encoded_credentials)