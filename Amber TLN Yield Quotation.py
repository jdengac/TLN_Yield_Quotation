import datetime
import hashlib
import hmac
import time
import urllib.parse

import pandas as pd
import requests
import config

#########Keys & URL########################################
Binance_API_KEY = config.Binance_keyPrivate
Binance_SECRET_KEY = config.Binance_keySecret
WhaleFin_API_Key = config.Whale_keyPrivate
WhaleFin_SECRET_KEY = config.Whale_keySecret
Binance_BASE_URL = 'https://api.binance.com'
Binance_PATH = '/sapi/v1/lending/project/list'
WhaleFin_BASE_URL = 'https://be.whalefin.com'
WhaleFin_PATH = '/api/v2/dual/yield'

amber_data_frame = pd.read_csv('AmberQuote.csv', header=0)
# print(amber_data_frame.iloc[0]['strike'])

timestamp = int(time.time() * 1000)
Col = ['Tenor (days)', 'Strike price discount', 'Annual yield']

# #Datetime -> HK_time
time = datetime.datetime.fromtimestamp(int(timestamp) / 1000)  # using the local timezone
Today_date = time.strftime("%Y-%m-%d")

aggregated_result_list = []

for row in range(len(amber_data_frame)):
    sublist = []
    strike = amber_data_frame.iloc[row]['strike']
    tenor = int(amber_data_frame.iloc[row]['tenor'])
    Target_time = (time + datetime.timedelta(days=tenor)).strftime("%Y-%m-%d")

    datetime_object = datetime.datetime.strptime(f'{Target_time} 16:00:00', '%Y-%m-%d %H:%M:%S')
    time_diff = (datetime_object - time).days + (datetime_object - time).seconds/60/60/24

    method = 'GET'

    params = urllib.parse.urlencode(
        {
            "strike": str(strike),
            'settleTime': f'{Target_time}T08:00:00.000Z',
            'symbol': 'USD_BTC'

        }
    )
    path = f'{WhaleFin_PATH}?{params}'

    signStr = f'method={method}&path={path}&timestamp={timestamp}'
    # method=GET&path=/api/v2/asset/statement?page=1&size=3&createStartTime=2022-03-06T03%3A00%3A00.000Z&timestamp=1646816265520

    signature = hmac.new(bytes(WhaleFin_SECRET_KEY, 'utf-8'), bytes(signStr, 'utf-8'), hashlib.sha256).hexdigest()

    headers = {
        'access-key': WhaleFin_API_Key,
        'access-timestamp': str(timestamp),
        'access-sign': signature
    }

    resp = requests.get(WhaleFin_BASE_URL + path, headers=headers)

    if resp.status_code == 200:
        Whale_r = resp.json()
        # interest = float(Whale_r['result']['interestRate'])
        # print(Whale_r)
        interest_rate = float(Whale_r["result"]["interestRate"])
        APY = interest_rate * 365 / time_diff
        APY_reformat = f'{"{:.2f}".format((APY*100))}%'
        # print(f'{"{:.2f}".format((APY*100))}%')
        # print(f'Maturity Date: {datetime_object}')
        print(f'Tenor: {tenor}, Strike: {strike}, APY: {APY_reformat}')
        sublist.append(tenor)
        sublist.append(strike)
        sublist.append(APY_reformat)
        aggregated_result_list.append(sublist)



    else:
        print(f'{resp.status_code}, WhaleFin API Call Failed')
        print(resp.text)

new_df = pd.DataFrame(columns=Col, data=aggregated_result_list).sort_values(by=['Tenor (days)'])
file_name = f'TLN_Yield_Quotation_{Today_date}.csv'
new_df.to_csv(f'TLN Yield Quotation/{file_name}', index=False)