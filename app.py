from flask import Flask, request, render_template, redirect, url_for
import requests
import json
import pandas
from datetime import date
import os

from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

accounts = []

@app.route('/trying', methods=['POST'])
def trying():
    symbol = request.form.get('symbol')
    order_type = request.form.get('order_type')
    instruction = request.form.get('instruction')
    
    # Accessing all checkbox values (as a list)
    accounts = request.form.getlist('accounts')

    # Accessing quantity and price inputs (assuming a known number of accounts or dynamically detecting them)
    quantities = []
    prices = []
    
    for key in request.form:
        if key.startswith('quantity_'):
            quantities.append(request.form.get(key))
        elif key.startswith('price_'):
            prices.append(request.form.get(key))

    #print(accounts)
    #print(quantities)
    #print(prices)

@app.route('/test')
def test():
    return render_template('test.html')


@app.route('/')
def index():
    return render_template('index.html')


def get_access_token():
    FILE_PATH = os.getenv("FILE_PATH")
    with open(FILE_PATH, 'r') as f:
        access_token = f.readline().strip()
    return access_token

def get_accounts(access_token):
    account_data = requests.get(
        url="https://api.schwabapi.com/trader/v1/accounts/accountNumbers",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    response_frame = pandas.json_normalize(account_data.json())
    accounts_list = response_frame.set_index('accountNumber')['hashValue'].to_dict()
    return accounts_list

def get_positions(access_token):
    access_token = get_access_token()
    accounts_list = get_accounts(access_token)

    account_info = {}
    for account, account_hash_value in accounts_list.items():
        account_info[account] = requests.get(
            url=f"https://api.schwabapi.com/trader/v1/accounts/{account_hash_value}",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"fields": "positions"}
        ).json()
    
    return account_info
    


def design_order(symbol, order_type, instruction, quantity, price, leg_id="1", order_leg_type="EQUITY", asset_type="EQUITY"):
    return {
        "price": price,
        "session": "NORMAL",
        "duration": "GOOD_TILL_CANCEL",
        "orderType": order_type,
        "complexOrderStrategyType": "NONE",
        "quantity": quantity,
        "taxLotMethod": "FIFO",
        "orderLegCollection": [
            {
                "orderLegType": order_leg_type,
                "legId": leg_id,
                "instrument": {
                    "symbol": symbol,
                    "assetType": asset_type,
                },
                "instruction": instruction,
                "positionEffect": "OPENING",
                "quantity": quantity,
            }
        ],
        "orderStrategyType": "SINGLE",
    }

@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        accounts = request.form.getlist('accounts')
        symbol = request.form.get('symbol')
        order_type = request.form.get('order_type')
        instruction = request.form.get('instruction')

        account_q_and_p = {}
        for key in request.form:
            if key.endswith('_quantity'):
                account_name = key.replace('_quantity', '')
                account_q_and_p.setdefault(account_name, {})['quantity'] = int(request.form.get(key))
            elif key.endswith('_price'):
                account_name = key.replace('_price', '')
                account_q_and_p.setdefault(account_name, {})['price'] = float(request.form.get(key))

        access_token = get_access_token()
        accounts_list = get_accounts(access_token)

        for account in accounts:
            account_hash_value = accounts_list.get(account)
            if account_hash_value and account_q_and_p[account]['price'] and account_q_and_p[account]['quantity']:
                post_order_payload = design_order(
                    symbol=symbol,
                    price=account_q_and_p[account]['price'],
                    order_type=order_type,
                    instruction=instruction,
                    quantity=account_q_and_p[account]['quantity'],
                )
                requests.post(
                    url=f"https://api.schwabapi.com/trader/v1/accounts/{account_hash_value}/orders",
                    headers={"Authorization": f"Bearer {access_token}", "accept": "*/*", 'Content-Type': 'application/json'},
                    data=json.dumps(post_order_payload)
                )

        return redirect(url_for('order'))
    
    return render_template('index.html')

@app.route('/getAccountNames', methods=['GET']) 
def getAccountNames():
    access_token = get_access_token()
    accounts_list = get_accounts(access_token)
    return accounts_list

@app.route('/getAccountInfo', methods=['GET']) 
def getAccountInfo():
    access_token = get_access_token()
    accounts_list = get_accounts(access_token)

    account_info = {}
    for account, account_hash_value in accounts_list.items():
        account_info[account] = requests.get(
            url=f"https://api.schwabapi.com/trader/v1/accounts/{account_hash_value}",
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()
    
    return account_info

@app.route('/getOrder', methods=['GET'])
def getOrder():
    access_token = get_access_token()
    accounts_list = get_accounts(access_token)

    today = f"{date.today()}T00:00:00.000Z"
    end_of_day = f"{date.today()}T23:59:59.000Z"

    orders = []
    for account_hash_value in accounts_list.values():
        orders.append(requests.get(
            url=f"https://api.schwabapi.com/trader/v1/accounts/{account_hash_value}/orders", 
            params={"fromEnteredTime": today, "toEnteredTime": end_of_day}, 
            headers={"Authorization": f"Bearer {access_token}"}
        ).json())

    return orders



if __name__ == '__main__':
   print(get_positions(get_access_token()))
   app.run(port=5000)