# Standard Library
import datetime
import time

from typing import Tuple

# Third Party
import jwt
import requests


URL = "http://127.0.0.1:5500/api/"

HEADERS = {"Content-Type": "application/json"}


class Authenticator:
    def __init__(self) -> None:
        self._user = "Sven"
        self._password = "1sven23"
        self._token = ""
        self._refresh = ""

    def login(self) -> None:
        json = {"username": self._user, "password": self._password}
        response = requests.request(
            method="POST", url=URL + "token/", headers=HEADERS, json=json, timeout=10,
        )
        if response.status_code == 200:
            print(response.json())
            self._token = response.json()["access"]
            self._refresh = response.json()["refresh"]
        else:
            print(response.status_code)

    def refresh_token(self) -> None:
        url = URL + "token/refresh/"
        json = {"refresh": self._refresh}
        response = requests.request(
            method="POST", url=url, headers=HEADERS, json=json, timeout=10,
        )

        if response.status_code == 200:
            print(response.json())
            self._token = response.json()["access"]
            self._refresh = response.json()["refresh"]
        else:
            print(response.status_code)

    def _original_request(self, url: str, config: dict) -> Tuple:
        url = URL + url
        response = requests.request(
            method=config["method"], url=url, headers=config["headers"], timeout=10,
        )
        data = response.json()
        return response, data

    def fetch(self, url) -> Tuple:
        config = {}
        decode = jwt.decode(self._token, options={"verify_signature": False})
        d = datetime.datetime.now()
        unixtime = time.mktime(d.timetuple())
        if (unixtime - decode["exp"]) > 1:
            self.refresh_token()
        config["method"] = "GET"
        config["headers"] = {
            "Authorization": "Bearer " + self._token,
            "Content-Type": "application/json",
        }

        respone, data = self._original_request(url=url, config=config)

        return respone, data

    def get_token(self) -> str:
        return self._token

    def set_token(self, token: str) -> None:
        self._token = token

    def get_refresh(self) -> str:
        return self._refresh

    def set_refresh(self, refresh: str) -> None:
        self._refresh = refresh
