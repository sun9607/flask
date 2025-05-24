import datetime
import os

import bcrypt
import pybase64
import requests


def get_signature():
    timestamp = int(datetime.datetime.now().timestamp() * 1000)
    password = os.getenv("NAVER_APPLICATION_ID") + "_" + str(timestamp)
    hashed = bcrypt.hashpw(password.encode("utf-8"), os.getenv("NAVER_APPLICATION_SECRET").encode("utf-8"))
    sign = pybase64.standard_b64encode(hashed).decode("utf-8")
    return sign, timestamp


def get_token():
    sign, timestamp = get_signature()
    url = f'https://api.commerce.naver.com/external/v1/oauth2/token'
    data = {
        "client_id": os.getenv("NAVER_APPLICATION_ID"),
        "timestamp": timestamp,
        "grant_type": "client_credentials",
        "client_secret_sign": sign,
        "type": "SELF"
    }
    response = requests.post(url, data=data)
    resp_data = response.json()
    access_token = resp_data.get("access_token")
    return access_token
