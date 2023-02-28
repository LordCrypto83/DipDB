#!/bin/bash
import sqlite3
from sqlite3 import Error
import requests
import numpy as np

API_KEY = ""

def create_connection():
    conn = None
    database = "db.db"
    try:
        conn = sqlite3.connect(database)
    except Error as e:
        return None
    return conn


def selectSQL(sqlStr):
    conn = create_connection()
    with conn:
        cur = conn.cursor()
        cur.execute(sqlStr)
        rows = cur.fetchall()
        return rows


def insertSQL(sqlStr, data):
    conn = create_connection()
    with conn:
        cur = conn.cursor()
        cur.execute(sqlStr, data)
        conn.commit()


def updateSQL(sqlStr, data):
    conn = create_connection()
    with conn:
        cur = conn.cursor()
        cur.execute(sqlStr, data)
        conn.commit()


def deleteSQL(sqlStr):
    conn = create_connection()
    with conn:
        cur = conn.cursor()
        cur.execute(sqlStr)
        conn.commit()

def get_address_data(address, chain):

    url = "https://deep-index.moralis.io/api/v2/erc20/metadata?chain=" + \
        chain+"&addresses="+address

    headers = {
        "accept": "application/json",
        "X-API-Key": ZhzUFfgUwK2cmJXa3gMeOxWlnskblcb1QFsiimPVuwPsfs6zb6j8KdUot4IqRDcj 
    }

    response = requests.get(url, headers=headers)
    try:
        # print(response.text)
        res = response.json()[0].get("symbol")
    except:
        return None
    return res


def get_token_price(address, chain):
    url = "https://deep-index.moralis.io/api/v2/erc20/"+address+"/price?chain="+chain

    headers = {
        "accept": "application/json",
        "X-API-Key": ZhzUFfgUwK2cmJXa3gMeOxWlnskblcb1QFsiimPVuwPsfs6zb6j8KdUot4IqRDcj 
    }

    response = requests.get(url, headers=headers)

    res = response.text

    if res.find("usdPrice") == -1:
        return None

    price = res.split("usdPrice\":")[1].split(",")[0]
    
    try:
        price = np.format_float_positional(float(price), trim='-')
        return str(price)
    except:
        return price


def token_check(address, chain):
    sqlStr = f"""SELECT * FROM tokens WHERE address='{address}'"""
    token = selectSQL(sqlStr)

    if not token:
        symb = get_address_data(address, chain)
        if symb:
            sqlStr = ''' INSERT INTO tokens(address,symbol,price,chain) VALUES(?,?,?,?) '''
            insertSQL(sqlStr, (address, symb, 0, chain))
            return symb
        return None
    symb = token[0][1]
    return symb


def user_check(user_id):
    sqlStr = f"""SELECT * FROM users WHERE id='{user_id}'"""
    rows = selectSQL(sqlStr)
    if not rows:
        sqlStr = ''' INSERT INTO users(id) VALUES(?) '''
        insertSQL(sqlStr, (user_id,))


def get_user_data(user_id):
    sqlStr = f"""SELECT * FROM users WHERE id='{user_id}'"""
    rows = selectSQL(sqlStr)
    return rows
