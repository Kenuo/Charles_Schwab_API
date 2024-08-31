from flask import Flask, request, render_template, redirect, url_for
import requests
import json
import pandas
from datetime import date
import os

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


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return render_template('test.html')


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
                if account_name not in account_q_and_p:
                    account_q_and_p[account_name] = {}
                account_q_and_p[account_name]['quantity'] = int(request.form.get(key))  # Assuming you want integers
            elif key.endswith('_price'):
                account_name = key.replace('_price', '')
                if account_name not in account_q_and_p:
                    account_q_and_p[account_name] = {}
                account_q_and_p[account_name]['price'] = float(request.form.get(key))  # Assuming you want floats

        #print(accounts)
        #print(account_q_and_p)

        def design_order(
                symbol,
                order_type,
                instruction,
                quantity,
                leg_id,
                order_leg_type,
                asset_type,
                price,
                session="NORMAL",
                duration="GOOD_TILL_CANCEL",
                complex_order_strategy_type="NONE",
                tax_lot_method="FIFO",
                position_effect="OPENING",
                order_strategy_type="SINGLE",
                ):

            post_order_payload = {
                "price": price,
                "session": session,
                "duration": duration,
                "orderType": order_type,
                "complexOrderStrategyType": complex_order_strategy_type,
                "quantity": quantity,
                "taxLotMethod": tax_lot_method,
                "orderLegCollection": [
                    {
                        "orderLegType": order_leg_type,
                        "legId": leg_id,
                        "instrument": {
                            "symbol": symbol,
                            "assetType": asset_type,
                        },
                        "instruction": instruction,
                        "positionEffect": position_effect,
                        "quantity": quantity,
                    }
                ],
                "orderStrategyType": order_strategy_type,
            }

            return post_order_payload
        
        FILE_PATH = os.getenv("FILE_PATH")

        with open(FILE_PATH, 'r') as f:
            access_token = f.readline()
        access_token = access_token[:-1]

        account_data = requests.get(url="https://api.schwabapi.com/trader/v1/accounts/accountNumbers", headers={"Authorization": f"Bearer {access_token}"})
        
        response_frame = pandas.json_normalize(account_data.json())
        accounts_list = response_frame.set_index('accountNumber')['hashValue'].to_dict()
        account_hash_value = response_frame["hashValue"].iloc[0]

        for account in accounts:
            account_hash_value = accounts_list[account]

            if account_q_and_p[account]['price'] != 0 and account_q_and_p[account]['quantity'] != 0:
                post_order_payload = design_order(
                            symbol=symbol,
                            price=account_q_and_p[account]['price'],
                            order_type=order_type,
                            instruction=instruction,
                            quantity=account_q_and_p[account]['quantity'],
                            leg_id="1",
                            order_leg_type="EQUITY",
                            asset_type="EQUITY",
                        )
            
                post_order_payload = json.dumps(post_order_payload)

                requests.post(url=f"https://api.schwabapi.com/trader/v1/accounts/{account_hash_value}/orders", headers={"Authorization": f"Bearer {access_token}", "accept": "*/*", 'Content-Type': 'application/json'}, data=post_order_payload)

        # After processing the POST request, redirect to the GET version of the page
        return redirect(url_for('order'))
    
    # Handle the GET request (render the form or return a simple message)
    return render_template('index.html')

@app.route('/getAccountNames', methods=['GET']) 
def getAccounts():
    FILE_PATH = os.getenv("FILE_PATH")
    with open(FILE_PATH, 'r') as f:
        access_token = f.readline()
    access_token = access_token[:-1]
    
    account_data = requests.get(url="https://api.schwabapi.com/trader/v1/accounts/accountNumbers", headers={"Authorization": f"Bearer {access_token}"})

    #converts JSON to Reponse frame and then to a list 
    response_frame = pandas.json_normalize(account_data.json())

    accounts_list = response_frame.set_index('accountNumber')['hashValue'].to_dict()
    
    return accounts_list

@app.route('/getAccountInfo', methods=['GET']) 
def getAccountInfo():
    FILE_PATH = os.getenv("FILE_PATH")
    with open(FILE_PATH, 'r') as f:
        access_token = f.readline()
    access_token = access_token[:-1]
    
    account_data = requests.get(url="https://api.schwabapi.com/trader/v1/accounts/accountNumbers", headers={"Authorization": f"Bearer {access_token}"})

    #converts JSON to Reponse frame and then to a list 
    response_frame = pandas.json_normalize(account_data.json())

    accounts_list = response_frame.set_index('accountNumber')['hashValue'].to_dict()

    account_info = {}
    
    for account in accounts_list:
        account_hash_value = accounts_list[account]

        account_info[account] = requests.get(url=f"https://api.schwabapi.com/trader/v1/accounts/{account_hash_value}", headers={"Authorization": f"Bearer {access_token}"}).json()
    
    return account_info

   

@app.route('/getOrder', methods=['GET'])
def getOrder():
    # ACCOUNT STUFF
    # gets accounts details
    FILE_PATH = os.getenv("FILE_PATH")
   
    # read the tokens in the file
    with open(FILE_PATH, 'r') as f:
        access_token = f.readline()
    access_token = access_token[:-1]

    # get all the account data
    account_data = requests.get(url="https://api.schwabapi.com/trader/v1/accounts/accountNumbers", headers={"Authorization": f"Bearer {access_token}"})

    #converts JSON to dictionary 
    response_frame = pandas.json_normalize(account_data.json())

    accounts_list = response_frame.set_index('accountNumber')['hashValue'].to_dict()
    #sets up hash value
    account_hash_value = response_frame["hashValue"].iloc[0]


    today = f"{date.today()}T00:00:00.000Z"
    end_of_day=f"{date.today()}T23:59:59.000Z"

    orders = []

    for account in accounts_list:
        account_hash_value = accounts_list[account]
        orders.append(requests.get(
            url=f"https://api.schwabapi.com/trader/v1/accounts/{account_hash_value}/orders", 
            params={"fromEnteredTime": today, "toEnteredTime": end_of_day}, 
            headers={"Authorization": f"Bearer {access_token}"}).json())


    #for o in orders:
        #print(o)
        #print('\n\n')

    return orders



if __name__ == '__main__':
   app.run(port=5000)