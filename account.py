import base64
import requests
import webbrowser
import time
import os 
from dotenv import load_dotenv

load_dotenv()

def write_in_file(access_token, refresh_token):
    file_path = "C:\\Users\\Ben's PC\\Documents\\Charles_Schwab_Python\\access_token_text"
    f = open(file_path, "w")
    f.write(f"{access_token}\n{refresh_token}")
    f.close()

def retrieve_tokens(app_key, encoded_credentials, callback_url):
    auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?client_id={app_key}&redirect_uri={callback_url}"

    # opens auth_url for user to sign into Charles Scwab
    webbrowser.open(auth_url)

    returned_url = input("----------------------\nEnter copied URL:\n----------------------\n")
    auth_code = f"{returned_url[returned_url.index('code=') + 5: returned_url.index('%40')]}@"

    # STEP 2
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": f"{auth_code}",
        "redirect_uri": f"{callback_url}"
    }

    response = requests.post(url="https://api.schwabapi.com/v1/oauth/token", data=data, headers=headers)
    #turns data into a dictionary
    response_json = response.json()


    refresh_token = ""
    access_token = ""

    for key in response_json:
        if key == "refresh_token":
            refresh_token = response_json[key]
        if key == "access_token":
            access_token = response_json[key]

    return access_token, refresh_token

def refresh_access_token(refresh_token, encoded_credentials):
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": f"{refresh_token}",
    }

    response = requests.post(url="https://api.schwabapi.com/v1/oauth/token", data=data, headers=headers)
    response_json = response.json()

    refresh_token = ""
    access_token = ""

    for key in response_json:
        if key == "refresh_token":
            refresh_token = response_json[key]
        if key == "access_token":
            access_token = response_json[key]

    write_in_file(access_token, refresh_token)

    print("-----------------\nTOKENS REFRESHED\n-----------------\n")

# retrieves tokens and then refreshes the access token every 29 minutes
if __name__ == '__main__':
    #STEP 1
    # APP_CALLBACK_URL
    callback_url = "https://127.0.0.1"

    # CONSUMER_KEY or Client_ID
    APP_KEY = os.getenv("APP_KEY")

    # Client_Secret
    SECRET_CODE = os.getenv("SECRET_CODE")
    
    # BASE64_ENCODED_Client_ID:Client_Secret
    credentials = f"{APP_KEY}:{SECRET_CODE}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    # Step 2
    access_token, refresh_token = retrieve_tokens(app_key=APP_KEY, encoded_credentials=encoded_credentials, callback_url=callback_url)

    write_in_file(access_token, refresh_token)

    # Step 4
    # stops the program for 29 minutes (1740 seconds)
    while True:
        time.sleep(1740)
        refresh_access_token(refresh_token=refresh_token, encoded_credentials=encoded_credentials)

        # Ctrl c to stop terminal from running
