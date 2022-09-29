import requests
import os 
import pickle
import urllib3
import json


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
CWD=os.getcwd()
SESSION_PATH = f"{CWD}/sessions.pickle"
TOKEN_PATH = f"{CWD}/usertoken.pickle"
OUTPUT_PATH = f"{CWD}/report.html"
TENBIS_FQDN = "https://www.10bis.co.il"
COUPONS_TYPES = [30, 40, 50, 100]
COUPONS_30 = "xxxxxxx"
COUPONS_40 = "xxxxxxx"
COUPONS_50 = "xxxxxxx"
COUPONS_100 = "xxxxxxx"
DEBUG = False

def get_coupons_mixture(budget):
    # credit to: https://stackoverflow.com/a/64409910
    min_coupon = budget
    if budget in COUPONS_TYPES:
        return 1, [budget]
    else:
        cl = []
        for coupon in COUPONS_TYPES:
            if coupon < budget:
                mt, t = get_coupons_mixture(budget - coupon)
                num_coupons = 1 + mt
                if num_coupons < min_coupon:
                    min_coupon = num_coupons
                    cl = t + [coupon]
    return min_coupon, cl

def main_procedure():
    # If token exists, use the token to authenticate 10bis
    if os.path.exists(SESSION_PATH) and os.path.exists(TOKEN_PATH):
        session = load_pickle(SESSION_PATH)
        user_token = load_pickle(TOKEN_PATH)
        session.user_token = user_token

    # If there's no token, authenticate 10bis and extract auth tokens
    else:
        session = auth_tenbis()
        create_pickle(session,SESSION_PATH)
    # get budget
    budget = get_available_budget(session)
    print(f"The available budget is: {budget}")
    if budget >= min(COUPONS_TYPES):
        print(f"Analyze your budget for optimal coupons mixture...")
        m, coupons_mixture = get_coupons_mixture(budget)
        num_of_coupons = len(coupons_mixture)
        print(f"Result: {num_of_coupons} coupons to buy: {coupons_mixture}")
        for coupon in range(0, len(coupons_mixture),1):
            print(f"Buying coupon #{coupon+1}: {coupons_mixture[coupon]}")
            #buy_coupon(session,coupons_mixture[coupon])
    else:
        print(f"Sorry, your budget ({budget}) is lower than the smallest available coupon ({min(COUPONS_TYPES)}).")

def input_number(message):
  while True:
    try:
       userInput = int(input(message))       
    except ValueError:
       print("Not an integer! Try again. (examples: 1,2,3,4,5)")
       continue
    else:
       return userInput 
       break 

def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def create_pickle(obj, path):
    with open(path, 'wb') as session_file:
        pickle.dump(obj, session_file)

def load_pickle(path):
    with open(path, 'rb') as session_file:
        objfrompickle = pickle.load(session_file)
        return objfrompickle

def get_available_budget(session):
    endpoint = TENBIS_FQDN + "/NextApi/UserTransactionsReport"
    payload = {"culture": "he-IL", "uiCulture": "he", "dateBias": 0}
    headers = {"content-type": "application/json", "user-token": session.user_token}
    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)

    if(DEBUG):
        print(endpoint + "\r\n" + str(response.status_code) + "\r\n"  + response.text)

    resp_json = json.loads(response.text)
    budget = resp_json['Data']['moneycards'][0]['balance']['monthly']
    return budget

def buy_coupon(session, coupon):
    endpoint = TENBIS_FQDN + f"/NextApi/GetOrderBarcode?culture=he-IL&uiCulture=he&orderId={coupon}&resId={coupon}"
    headers = {"content-type": "application/json"}
    headers.update({'user-token': session.user_token})
    response = session.get(endpoint, headers=headers, verify=False)
    resp_json = json.loads(response.text)
    if(DEBUG):
        print(endpoint + "\r\n" + str(response.status_code) + "\r\n"  + response.text)
    used = resp_json['Data']['Vouchers'][0]['Used']

    if not used:
        barcode_number = resp_json['Data']['Vouchers'][0]['BarCodeNumber']
        barcode_number_formatted = '-'.join(barcode_number[i:i+4] for i in range(0, len(barcode_number), 4))
        barcode_img_url = resp_json['Data']['Vouchers'][0]['BarCodeImgUrl']
        amount = resp_json['Data']['Vouchers'][0]['Amount']
        valid_date = resp_json['Data']['Vouchers'][0]['ValidDate']
        return used, barcode_number_formatted, barcode_img_url, amount, valid_date

    return used, '', '', '', ''

def auth_tenbis():
    # Phase one -> Email
    email = input("Enter email: ")
    endpoint = TENBIS_FQDN + "/NextApi/GetUserAuthenticationDataAndSendAuthenticationCodeToUser"

    payload = {"culture": "he-IL", "uiCulture": "he", "email": email}
    headers = {"content-type": "application/json"}
    session = requests.session()

    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    resp_json = json.loads(response.text)

    if(DEBUG):
        print(endpoint + "\r\n" + str(response.status_code) + "\r\n"  + response.text)

    if (200 <= response.status_code <= 210):
        print("login successful")
    else:
        print("login failed")

    # Phase two -> OTP
    endpoint = TENBIS_FQDN + "/NextApi/GetUserV2"
    auth_token =  resp_json['Data']['codeAuthenticationData']['authenticationToken']
    shop_cart_guid = resp_json['ShoppingCartGuid']

    otp = input("Enter OTP: ")
    payload = {"shoppingCartGuid": shop_cart_guid,
                "culture":"he-IL",
                "uiCulture":"he",
                "email": email,
                "authenticationToken": auth_token,
                "authenticationCode": otp}

    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    resp_json = json.loads(response.text)
    user_token = resp_json['Data']['userToken']

    create_pickle(user_token, TOKEN_PATH)
    session.user_token = user_token

    if(DEBUG):
        print(endpoint + "\r\n" + str(response.status_code) + "\r\n"  + response.text)
        print(session)

    return session

if __name__ == '__main__':
    main_procedure()
