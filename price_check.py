#!/bin/bash
from bot_functions import *
import requests
import time


def notify_user(chat_id, message):
    url = "https://api.telegram.org/bot5822526647:AAH6RN6bHJGcaIHdWZLmCjx6gs_ofGMMMgY/sendMessage"

    payload = {
        "text": message,
        "disable_web_page_preview": False,
        "disable_notification": False,
        "reply_to_message_id": None,
        "chat_id": chat_id
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    print(response.text)


def clean_db():
    address_list = []
    for a in selectSQL("""SELECT address FROM users """):
        address_list.append(a[0])
    address_set = set(address_list)

    token_list = []
    for t in selectSQL("""SELECT address FROM tokens """):
        token_list.append(t[0])
    token_set = set(token_list)

    differences = address_set ^ token_set

    if len(differences) > 0:
        for d in differences:
            print(f"Removing unused token: {d}")
            deleteSQL(f"""Delete FROM tokens where address = '{d}' """)


def update_prices():
    token_list = []
    for address, chain in selectSQL("""SELECT address, chain FROM tokens """):
        token_list.append(address)
        price = get_token_price(address, chain)
        if price:
            sqlStr = """UPDATE tokens set price = ? where address = ?"""
            updateSQL(sqlStr, (price, address))


def dip_check():
    user_data = selectSQL("""SELECT id, address, dip_price FROM users """)
    token_data = selectSQL("""SELECT address, symbol, price FROM tokens """)
    for address, symbol, price in token_data:
        for id, user_address, dip_price in user_data:
            if address == user_address:
                if dip_price == None:
                    return
                print(f"\nUser ID: {id}\nToken Address: {address}\nSymbol: {symbol}\nPrice: {price},\nDip Price: {dip_price}")
                if float(dip_price) > float(price):
                    notify_user(
                        id, f"\U00002757\U00002757\U00002757DIP DETECTED\U00002757\U00002757\U00002757\nToken Address: {address}\nSymbol: {symbol}\nCurrent Price: {price}\nDip Price: {dip_price}")
                    deleteSQL(f"""Delete FROM users where id = '{id}' """)


while True:
    print("\nCleaning DB...")
    clean_db()
    print("Updating prices...")
    update_prices()
    print("Checking for Dips...")
    dip_check()
    print("\n")
    time.sleep(60)
