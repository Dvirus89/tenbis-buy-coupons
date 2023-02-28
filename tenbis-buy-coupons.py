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
COUPONS_IDS = {
    30:2046839,
    40:2046840,
    50:2046841,
    100:2046845
}
DEBUG = True

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
    #if os.path.exists(SESSION_PATH) and os.path.exists(TOKEN_PATH):
        #session = load_pickle(SESSION_PATH)
        #user_token = load_pickle(TOKEN_PATH)
        #session.user_token = user_token

    # If there's no token, authenticate 10bis and extract auth tokens
    #else:
        #session = auth_tenbis()
        #create_pickle(session,SESSION_PATH)
    session = auth_tenbis()
    # get budget
    budget = get_available_budget(session)
    budget = 50 # remove later
    print(f"The available budget is: {budget}")
    if budget >= min(COUPONS_TYPES):
        print(f"Analyze your budget for optimal coupons mixture...")
        
        m, coupons_mixture = get_coupons_mixture(budget)
        num_of_coupons = len(coupons_mixture)
        print(f"Result: {num_of_coupons} coupons to buy: {coupons_mixture}")
        for coupon in range(0, len(coupons_mixture),1):
            print(f"Buying coupon #{coupon+1}: {coupons_mixture[coupon]}")
            #get_shopping_card_guid(session)
            buy_coupon(session,coupons_mixture[coupon])
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
        input("wait log UserTransactionsReport")
    resp_json = json.loads(response.text)
    budget = resp_json['Data']['moneycards'][0]['balance']['monthly']
    return budget

def buy_coupon(session, coupon):
    # add to shopping cart
    # SetAddressInOrder
    #
    endpoint = TENBIS_FQDN + f"/NextApi/SetAddressInOrder"
    headers = {"content-type": "application/json"}
    headers.update({'user-token': session.user_token})
    payload = {"shoppingCartGuid":session.cart_guid,"culture":"he-IL","uiCulture":"he","addressId":9181057,"cityId":37,"cityName":"ראש העין","streetId":48741,"streetName":"ניסים אלוני","houseNumber":"2","apartmentNumber":"","entrance":"","floor":"","comments":"","longitude":34.9798421,"latitude":32.0849931,"nameOnDoor":"","phone01":"0522222222","phone02":"0522222222","isCompanyAddress":False,"addressCompanyId":0,"locationType":"residential","locationName":"","restaurantDeliversToAddress":False,"shiftId":0,"addressKey":"37-48741-2-9181057"}
    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    resp_json = json.loads(response.text)
    if(DEBUG):
        print("Request:\r\n" + endpoint + "\r\n"  + json.dumps(payload) + "\r\n########")
        print("Response: " + str(response.status_code) + "\r\n")
        print(resp_json)
        input("wait log SetAddressInOrder")

    # SetDeliveryMethodInOrder
    #
    endpoint = TENBIS_FQDN + f"/NextApi/SetDeliveryMethodInOrder"
    headers = {"content-type": "application/json"}
    headers.update({'user-token': session.user_token})
    payload = {"shoppingCartGuid":session.cart_guid,"culture":"he-IL","uiCulture":"he","deliveryMethod":"delivery"}
    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    resp_json = json.loads(response.text)
    if(DEBUG):
        print("Request:\r\n" + endpoint + "\r\n"  + json.dumps(payload) + "\r\n########")
        print("Response: " + str(response.status_code) + "\r\n")
        print(resp_json)
        input("wait log SetDeliveryMethodInOrder")

    # SetRestaurantInOrder
    #
    endpoint = TENBIS_FQDN + f"/NextApi/SetRestaurantInOrder"
    headers = {"content-type": "application/json"}
    headers.update({'user-token': session.user_token})
    payload = {"shoppingCartGuid":session.cart_guid,"culture":"he-IL","uiCulture":"he","isMobileDevice":True,"restaurantId":"26698"}
    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    resp_json = json.loads(response.text)
    if(DEBUG):
        print("Request:\r\n" + endpoint + "\r\n"  + json.dumps(payload) + "\r\n########")
        print("Response: " + str(response.status_code) + "\r\n")
        print(resp_json)
        input("wait log SetRestaurantInOrder")
    
    # SetDishListInShoppingCart
    #
    endpoint = TENBIS_FQDN + f"/NextApi/SetDishListInShoppingCart"
    headers = {"content-type": "application/json"}
    headers.update({'user-token': session.user_token})
    print(str(coupon) + " " + session.cart_guid + " " + str(session.user_id))
    payload = {"shoppingCartGuid": session.cart_guid,
               "culture":"he-IL",
               "uiCulture":"he",
               "dishList":[{"dishId":COUPONS_IDS[coupon],"shoppingCartDishId":1,"quantity":1,"assignedUserId":session.user_id,"choices":[],"dishNotes":None,"categoryId":278344}]}

    print(json.dumps(payload))
    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    resp_json = json.loads(response.text)
    if(DEBUG):
        print("Request:\r\n" + endpoint + "\r\n"  + json.dumps(payload) + "\r\n########")
        print("Response: " + str(response.status_code) + "\r\n")
        print(resp_json)
        input("wait log SetDishListInShoppingCart")

# GetPayments
    #
    endpoint = TENBIS_FQDN + f"/NextApi/GetPayments?shoppingCartGuid={session.cart_guid}&culture=he-IL&uiCulture=he"
    headers = {"content-type": "application/json"}
    headers.update({'user-token': session.user_token})
    response = session.get(endpoint, headers=headers, verify=False)
    resp_json = json.loads(response.text)
    main_user=current = [x for x in resp_json['Data'] if x['userId'] == session.user_id]
    # TODO - make sure to use only 10BIS cards
    if(DEBUG):
        print("Request:\r\n" + endpoint + "\r\n########")
        print("Response: " + str(response.status_code) + "\r\n")
        print(resp_json)
        input("wait log GetPayments")

    # SetPaymentsInOrder
    #
    endpoint = TENBIS_FQDN + f"/NextApi/SetPaymentsInOrder"
    headers = {"content-type": "application/json"}
    headers.update({'user-token': session.user_token})
    payload = {"shoppingCartGuid":session.cart_guid,"culture":"he-IL","uiCulture":"he","payments":[{"paymentMethod":"Moneycard","creditCardType":"none","cardId":main_user[0]['cardId'],"cardToken":"","userId":session.user_id,"userName":main_user[0]['userName'],"cardLastDigits":main_user[0]['cardLastDigits'],"sum":coupon,"assigned":True,"remarks":None,"expirationDate":None,"isDisabled":False,"editMode":False}]}
    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    resp_json = json.loads(response.text)
    if(DEBUG):
        print("Request:\r\n" + endpoint + "\r\n"  + json.dumps(payload) + "\r\n########")
        print("Response: " + str(response.status_code) + "\r\n")
        print(resp_json)
        input("wait log SetPaymentsInOrder")

    # SubmitOrder
    #
    endpoint = TENBIS_FQDN + f"/NextApi/SubmitOrder"
    headers = {"content-type": "application/json"}
    headers.update({'user-token': session.user_token})
    payload = {"shoppingCartGuid":session.cart_guid,"culture":"he-IL","uiCulture":"he","isMobileDevice":True,"dontWantCutlery":False,"orderRemarks":None}
    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    resp_json = json.loads(response.text)
    if(DEBUG):
        print("Request:\r\n" + endpoint + "\r\n"  + json.dumps(payload) + "\r\n########")
        print("Response: " + str(response.status_code) + "\r\n")
        print(resp_json)
        input("wait log SubmitOrder")


def get_shopping_card_guid(session):
    endpoint = TENBIS_FQDN + "/"
    headers = {"content-type": "application/json"}
    #headers.update({'user-token': session.user_token})
    response = session.get(endpoint, verify=False)
    #resp_json = json.loads(response.text)
    if(DEBUG):
        print(response.headers)
        print(endpoint + "\r\n" + str(response.status_code) + "\r\n"  + response.text)



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
    otp = input("Enter OTP: ")
    payload = {"shoppingCartGuid": "00000000-0000-0000-0000-000000000000",
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
    session.cart_guid = resp_json['ShoppingCartGuid']
    session.user_id = resp_json['Data']['userId']
    if(DEBUG):
        print(endpoint + "\r\n" + str(response.status_code) + "\r\n"  + response.text)
        print(session)
        input("wait log GetUserV2")

    return session

if __name__ == '__main__':
    main_procedure()
