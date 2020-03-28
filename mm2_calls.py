#!/usr/bin/env python3
import os
import json
import time
import requests
from subprocess import Popen
from lib import coinslib


cwd = os.getcwd()
mm2_path = os.path.dirname(os.path.abspath(__file__))
mm2log_path = os.path.dirname(os.path.abspath(__file__)) + "/logs"

with open(mm2_path+"/MM2.json") as j:
    mm2json = json.load(j)
    
if mm2json['passphrase'] == "":
    print("Please edit 'MM2.json' with your passphrase (seed).")
    exit()

user_pass = mm2json['rpc_password']
node_ip = "http://127.0.0.1:7783"

def help_mm2(node_ip, user_pass):
    params = {'userpass': user_pass, 'method': 'help'}
    r = requests.post(node_ip, json=params, timeout=60)
    return r.text

def check_mm2_status(node_ip, user_pass):
    try:
        help_mm2(node_ip, user_pass)
        return True
    except Exception as e:
        return False

def start_mm2(logfile):
    mm2_output = open(logfile, 'w+')
    os.chdir(mm2_path)
    Popen(["./mm2"], stdout=mm2_output, stderr=mm2_output, universal_newlines=True)
    print("Marketmaker 2 started. Use 'tail -f "+logfile+"' for mm2 console messages.")
    os.chdir(cwd)

def stop_mm2(node_ip=node_ip, user_pass=user_pass):
    params = {'userpass': user_pass, 'method': 'stop'}
    try:
        r = requests.post(node_ip, json=params, timeout=60)
        print("Marketmaker 2 stopped. ")
    except:
        print("Marketmaker 2 was not running. ")

def activate_all(node_ip=node_ip, user_pass=user_pass):
    for coin in coinslib.coins:
        if coinslib.coins[coin]['activate_with'] == 'native':
            r = enable(node_ip, user_pass, coin)
        else:
            r = electrum(node_ip, user_pass, coin)


def enable(node_ip, user_pass, cointag, tx_history=True):
    coin = coinslib.coins[cointag]
    params = {'userpass': user_pass,
              'method': 'enable',
              'coin': cointag,
              'mm2':1,
              'tx_history':tx_history,}
    r = requests.post(node_ip, json=params, timeout=60)
    return r

def electrum(node_ip, user_pass, cointag, tx_history=True):
    coin = coinslib.coins[cointag]
    if 'contract' in coin:
        params = {'userpass': user_pass,
                  'method': 'enable',
                  'urls': coin['electrum'],
                  'coin': cointag,
                  'swap_contract_address': coin['contract'],
                  'mm2': 1,
                  'tx_history': tx_history}
    else:
        params = {'userpass': user_pass,
                  'method': 'electrum',
                  'servers': coin['electrum'],
                  'coin': cointag,
                  'mm2': 1,
                  'tx_history': tx_history}
    r = requests.post(node_ip, json=params, timeout=60)
    return r

def orderbook(node_ip=node_ip, user_pass=user_pass, base="KMD", rel="BTC"):
    params = {'userpass': user_pass,
              'method': 'orderbook',
              'base': base, 'rel': rel}
    r = requests.post(node_ip, json=params, timeout=60)
    return r

def get_orders_json(node_ip=node_ip, user_pass=user_pass, coins=coinslib.coins):
    orders = []
    ask_json = []
    bid_json = []
    for base in coins:
        for rel in coins:
            if base != rel:
                orderbook_response = orderbook(node_ip, user_pass, base, rel).json()
                orders.append(orderbook_response)
    for pair in orders:
        if 'asks' in pair:
            if len(pair['asks']) > 0:
                baserel = pair['rel']+"/"+pair['base']
                for ask in pair['asks']:
                    baserel = pair['base']+"/"+pair['rel']
                    ask_json.append({"pair": baserel, "price": str("%0.12f" % float(ask['price']))[:12], "volume": str("%0.12f" % float(ask['maxvolume']))[:12]})
                for bid in pair['bids']:
                    bid_json.append({"baserel": baserel, "price": str("%0.12f" % float(bid['price']))[:12], "volume": str("%0.12f" % float(bid['maxvolume']))[:12]})
    return ask_json, bid_json

def my_balance(cointag, node_ip=node_ip, user_pass=user_pass):
    params = {'userpass': user_pass,
              'method': 'my_balance',
              'coin': cointag}
    r = requests.post(node_ip, json=params, timeout=60)
    return r

def buy(base, rel, basevolume, relprice, node_ip=node_ip, user_pass=user_pass):
    params = {'userpass': user_pass,
             'method': 'buy',
             'base': base,
             'rel': rel,
             'volume': basevolume,
             'price': relprice}
    r = requests.post(node_ip, json=params, timeout=60)
    return r

def my_orders(node_ip=node_ip, user_pass=user_pass):
    params = {'userpass': user_pass,
              'method': 'my_orders'}
    r = requests.post(node_ip, json=params, timeout=60)
    return r

def my_recent_swaps(node_ip=node_ip, user_pass=user_pass, limit=10, from_uuid=''):
    if from_uuid == '':
        params = {'userpass': user_pass,
                  'method': 'my_recent_swaps',
                  'limit': int(limit)}
    else:
        params = {'userpass': user_pass,
                  'method': 'my_recent_swaps',
                  "limit": int(limit),
                  "from_uuid": from_uuid}
    r = requests.post(node_ip, json=params, timeout=60)
    return r

def cancel_all(node_ip=node_ip, user_pass=user_pass):
    params = {'userpass': user_pass,
              'method': 'cancel_all_orders',
              'cancel_by': {"type": "All"}}
    r = requests.post(node_ip, json=params, timeout=60)
    return r

def cancel_uuid(order_uuid, node_ip=node_ip, user_pass=user_pass):
    params = {'userpass': user_pass,
              'method': 'cancel_order',
              'uuid': order_uuid}
    r = requests.post(node_ip, json=params, timeout=60)
    return r

def withdraw_all(cointag, address, node_ip=node_ip, user_pass=user_pass):
    params = {'userpass': user_pass,
              'method': 'withdraw',
              'coin': cointag,
              'to': address,
              'max': True}
    r = requests.post(node_ip, json=params, timeout=60)
    return r

def send_raw_transaction(cointag, tx_hex, node_ip=node_ip, user_pass=user_pass):
    params = {'userpass': user_pass,
              'method': 'send_raw_transaction',
              'coin': cointag,
              'tx_hex': tx_hex}
    r = requests.post(node_ip, json=params, timeout=60)
    return r

def get_trade_fee(cointag, node_ip=node_ip, user_pass=user_pass):
    params = {'userpass': user_pass,
              'method': 'get_trade_fee',
              'coin': cointag}
    r = requests.post(node_ip, json=params, timeout=60)
    return r


mm2_running = check_mm2_status(node_ip, user_pass)

if mm2_running:
    print("Marketmaker 2 is running.")
    activate_all(node_ip, user_pass)
else:
    start_mm2('mm2.log')
    time.sleep(8)
    activate_all(node_ip, user_pass)
    pass

if __name__ == '__main__':
    print(get_trade_fee("BTC").text)
