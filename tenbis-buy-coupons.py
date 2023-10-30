import requests
import urllib3
import json
import time

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
TENBIS_FQDN = "https://www.10bis.co.il"
COUPONS_TYPES = [200, 100, 50, 40, 30, 15, 1] # "1" added as a dummy coin
COUPONS_IDS = {
    15:6552646,
    30:2046839,
    40:2046840,
    50:2046841,
    100:2046845,
    200: 6552647
}
DEBUG = False
DRYRUN = False

def get_coupons_mixture(budget):
    # Create a table to store the minimum number of coupons required to make up each sub-amount
    max_value = 10 ** 5  # Set a maximum value that is greater than the maximum budget
    table = [max_value] * (budget + 1)
    table[0] = 0
    # Calculate the minimum number of coupons required for each sub-amount
    for i in range(1, budget + 1):
        for coupon in COUPONS_TYPES:
            if coupon <= i:
                subproblem = table[i - coupon]
                if subproblem != max_value and subproblem + 1 < table[i]:
                    table[i] = subproblem + 1
    # Get the list of coupons required to make up the minimum number
    coupons = []
    i = budget
    while i > 0 and i >= min(COUPONS_TYPES):
        for coupon in COUPONS_TYPES:
            if coupon <= i and table[i - coupon] == table[i] - 1:
                if coupon !=1: # Ignore dummy "coins"
                    coupons.append(coupon)
                i -= coupon
                break
    # Return the minimum number of coupons and the list of coupons required
    return int(len(coupons)), [int(coupon) for coupon in coupons]

def input_budget_validation(budget):
  while True:
    try:
       userInput = float(input(f"Enter the amount you wish to spend on Shufersal coupons: [{budget}] ") or str(budget))
       if userInput > budget:
              print(f"The amount you entered ({userInput}) is higher then the actual budget({budget})")
              continue   
    except ValueError:
       print("Not valid amount! Try again. (examples: 50, 98.50, 200, 1000)")
       continue
    else:
       return userInput 
       break     

def sleep_print(seconds):
    for i in range(seconds,0,-1):
        print(f"     countdown: {i}     ", end="\r", flush=True)
        time.sleep(1)

def print_hebrew(heb_txt):
    print(heb_txt[::-1])

def main_procedure():
    session = auth_tenbis()
    if(not session):
        print("exit")
        return
    # get budget
    budget = get_available_budget(session)
    print(f"The available budget is: {budget}")
    budget = input_budget_validation(budget)
    if budget >= 30:
        print(f"Analyze your budget for optimal coupons mixture...")
        num_of_coupons, coupons_mixture = get_coupons_mixture(int(budget))
        print(f"Result: {num_of_coupons} coupons to buy: {coupons_mixture}")
        if input("Press ENTER to continue or type 'no' to cancel: ") == "":
            for i in range(0, len(coupons_mixture),1):
                if (i > 0 and int(coupons_mixture[i]) == int(coupons_mixture[i-1])):
                    print("waiting the required time before two identical orders...\r\n")
                    sleep_print(130)
                print(f"Buying coupon #{i+1}: {coupons_mixture[i]}")
                buy_coupon(session,coupons_mixture[i])
            print("Mission complete :)")
        else:
            print("canceled.")
    else:
        print(f"Sorry, your budget ({budget}) is lower than the smallest available coupon ({min(COUPONS_TYPES)}).")

def get_available_budget(session):
    endpoint = TENBIS_FQDN + "/NextApi/UserTransactionsReport"
    payload = {"culture": "he-IL", "uiCulture": "he", "dateBias": 0}
    headers = {"content-type": "application/json", "user-token": session.user_token}
    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    if(DEBUG):
        print(endpoint + "\r\n" + str(response.status_code) + "\r\n"  + response.text)
        print("wait log UserTransactionsReport")
    resp_json = json.loads(response.text)
    budget = resp_json['Data']['moneycards'][0]['balance']['monthly']
    return budget

def buy_coupon(session, coupon):
    endpoint = TENBIS_FQDN + f"/NextApi/SetAddressInOrder"
    headers = {"content-type": "application/json"}
    headers.update({'user-token': session.user_token})
    payload = {"shoppingCartGuid":session.cart_guid,"culture":"he-IL","uiCulture":"he","addressId":9181057,"cityId":37,"cityName":"ראש העין","streetId":48741,"streetName":"ניסים אלוני","houseNumber":"2","apartmentNumber":"","entrance":"","floor":"","comments":"","longitude":34.9798421,"latitude":32.0849931,"nameOnDoor":"","phone01":"0522222222","phone02":"0522222222","isCompanyAddress":False,"addressCompanyId":0,"locationType":"residential","locationName":"","restaurantDeliversToAddress":False,"shiftId":0,"addressKey":"37-48741-2-9181057"}
    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    resp_json = json.loads(response.text)
    error_msg = resp_json['Errors']
    success_code = resp_json['Success']
    if(not success_code):
        print_hebrew((error_msg[0]['ErrorDesc']))
        return
    if(DEBUG):
        print("Request:\r\n" + endpoint + "\r\n"  + json.dumps(payload) + "\r\n########")
        print("Response: " + str(response.status_code) + "\r\n")
        print(resp_json)
        print("wait log SetAddressInOrder")

    # SetDeliveryMethodInOrder
    #
    endpoint = TENBIS_FQDN + f"/NextApi/SetDeliveryMethodInOrder"
    headers = {"content-type": "application/json"}
    headers.update({'user-token': session.user_token})
    payload = {"shoppingCartGuid":session.cart_guid,"culture":"he-IL","uiCulture":"he","deliveryMethod":"delivery"}
    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    resp_json = json.loads(response.text)
    error_msg = resp_json['Errors']
    success_code = resp_json['Success']
    if(not success_code):
        print_hebrew((error_msg[0]['ErrorDesc']))
        return
    if(DEBUG):
        print("Request:\r\n" + endpoint + "\r\n"  + json.dumps(payload) + "\r\n########")
        print("Response: " + str(response.status_code) + "\r\n")
        print(resp_json)
        print("wait log SetDeliveryMethodInOrder")

    # SetRestaurantInOrder
    #
    endpoint = TENBIS_FQDN + f"/NextApi/SetRestaurantInOrder"
    headers = {"content-type": "application/json"}
    headers.update({'user-token': session.user_token})
    payload = {"shoppingCartGuid":session.cart_guid,"culture":"he-IL","uiCulture":"he","isMobileDevice":True,"restaurantId":"26698"}
    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    resp_json = json.loads(response.text)
    error_msg = resp_json['Errors']
    success_code = resp_json['Success']
    if(not success_code):
        print_hebrew((error_msg[0]['ErrorDesc']))
        return
    if(DEBUG):
        print("Request:\r\n" + endpoint + "\r\n"  + json.dumps(payload) + "\r\n########")
        print("Response: " + str(response.status_code) + "\r\n")
        print(resp_json)
        print("wait log SetRestaurantInOrder")
    
    # SetDishListInShoppingCart
    #
    endpoint = TENBIS_FQDN + f"/NextApi/SetDishListInShoppingCart"
    headers = {"content-type": "application/json"}
    headers.update({'user-token': session.user_token})
    payload = {"shoppingCartGuid": session.cart_guid,
               "culture":"he-IL",
               "uiCulture":"he",
               "dishList":[{"dishId":COUPONS_IDS[int(coupon)],"shoppingCartDishId":1,"quantity":1,"assignedUserId":session.user_id,"choices":[],"dishNotes":None,"categoryId":278344}]}
    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    resp_json = json.loads(response.text)
    error_msg = resp_json['Errors']
    success_code = resp_json['Success']
    if(not success_code):
        print_hebrew((error_msg[0]['ErrorDesc']))
        return
    if(DEBUG):
        print("Request:\r\n" + endpoint + "\r\n"  + json.dumps(payload) + "\r\n########")
        print("Response: " + str(response.status_code) + "\r\n")
        print(resp_json)
        print("wait log SetDishListInShoppingCart")

    # GetPayments
    #
    endpoint = TENBIS_FQDN + f"/NextApi/GetPayments?shoppingCartGuid={session.cart_guid}&culture=he-IL&uiCulture=he"
    headers = {"content-type": "application/json"}
    headers.update({'user-token': session.user_token})
    response = session.get(endpoint, headers=headers, verify=False)
    resp_json = json.loads(response.text)
    # TODO - make sure to use only 10BIS cards
    error_msg = resp_json['Errors']
    success_code = resp_json['Success']
    if(not success_code):
        print_hebrew((error_msg[0]['ErrorDesc']))
        return
    if(DEBUG):
        print("Request:\r\n" + endpoint + "\r\n########")
        print("Response: " + str(response.status_code) + "\r\n")
        print(resp_json)
        print("wait log GetPayments")
    main_user=current = [x for x in resp_json['Data'] if x['userId'] == session.user_id]

    # SetPaymentsInOrder
    #
    endpoint = TENBIS_FQDN + f"/NextApi/SetPaymentsInOrder"
    headers = {"content-type": "application/json"}
    headers.update({'user-token': session.user_token})
    payload = {"shoppingCartGuid":session.cart_guid,"culture":"he-IL","uiCulture":"he","payments":[{"paymentMethod":"Moneycard","creditCardType":"none","cardId":main_user[0]['cardId'],"cardToken":"","userId":session.user_id,"userName":main_user[0]['userName'],"cardLastDigits":main_user[0]['cardLastDigits'],"sum":coupon,"assigned":True,"remarks":None,"expirationDate":None,"isDisabled":False,"editMode":False}]}
    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    resp_json = json.loads(response.text)
    error_msg = resp_json['Errors']
    success_code = resp_json['Success']
    if(not success_code):
        print_hebrew((error_msg[0]['ErrorDesc']))
        return
    if(DEBUG):
        print("Request:\r\n" + endpoint + "\r\n"  + json.dumps(payload) + "\r\n########")
        print("Response: " + str(response.status_code) + "\r\n")
        print(resp_json)
        print("wait log SetPaymentsInOrder")


    if DRYRUN:
        return
    # SubmitOrder
    #
    endpoint = TENBIS_FQDN + f"/NextApi/SubmitOrder"
    headers = {"content-type": "application/json"}
    headers.update({'user-token': session.user_token})
    payload = {"shoppingCartGuid":session.cart_guid,"culture":"he-IL","uiCulture":"he","isMobileDevice":True,"dontWantCutlery":False,"orderRemarks":None}
    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    resp_json = json.loads(response.text)
    error_msg = resp_json['Errors']
    success_code = resp_json['Success']
    if(not success_code):
        print_hebrew((error_msg[0]['ErrorDesc']))
        return
    if(DEBUG):
        print("Request:\r\n" + endpoint + "\r\n"  + json.dumps(payload) + "\r\n########")
        print("Response: " + str(response.status_code) + "\r\n")
        print(resp_json)
        print("wait log SubmitOrder")
    session.cart_guid = resp_json['ShoppingCartGuid']

def auth_tenbis():
    # Phase one -> Email
    email = input("Enter email: ")
    endpoint = TENBIS_FQDN + "/NextApi/GetUserAuthenticationDataAndSendAuthenticationCodeToUser"
    payload = {"culture": "he-IL", "uiCulture": "he", "email": email}
    headers = {"content-type": "application/json"}
    session = requests.session()

    response = session.post(endpoint, data=json.dumps(payload), headers=headers, verify=False)
    resp_json = json.loads(response.text)
    error_msg = resp_json['Errors']

    if(DEBUG):
        print(endpoint + "\r\n" + str(response.status_code) + "\r\n"  + response.text)

    if (200 <= response.status_code <= 210 and (len(error_msg) == 0)):
        print("User exist, next step is...")
    else:
        print("login failed")
        print_hebrew((error_msg[0]['ErrorDesc']))
        return False

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
    error_msg = resp_json['Errors']
    user_token = resp_json['Data']['userToken']
    session.user_token = user_token
    session.cart_guid = resp_json['ShoppingCartGuid']
    session.user_id = resp_json['Data']['userId']
    if(DEBUG):
        print(endpoint + "\r\n" + str(response.status_code) + "\r\n"  + response.text)
        print(session)
        print("wait log GetUserV2")

    if (200 <= response.status_code <= 210 and (len(error_msg) == 0)):
        print("login successful...")
    else:
        print("login failed")
        print_hebrew((error_msg[0]['ErrorDesc']))
        return False

    return session

if __name__ == '__main__':
    main_procedure()
