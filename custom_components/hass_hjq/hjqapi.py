import asyncio
import hashlib
import json
import logging
import threading
import time
import urllib.parse

import aiohttp
import httpx

_LOGGER = logging.getLogger(__name__)


class HJQApi:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(HJQApi, cls).__new__(cls)
        return cls._instance

    def __init__(self, tel: str, pwd: str):
        if not hasattr(self, "initialized"):
            self.tel = tel
            self.pwd = pwd
            self.hjq_token = None
            self.pass_id = None
            self.auth = None
            self.initialized = True

    async def get_hjqtoken_passid(self):
        if self.hjq_token and self.pass_id:
            return self.hjq_token, self.pass_id

        api = "https://base.hjq.komect.com/base/user/passwdLogin"
        body = json.dumps(
            {
                "virtualAuthdata": self.get_md5(self.pwd),
                "authType": "10",
                "userAccount": self.tel,
                "authdata": self.get_sha1("fetion.com.cn:" + self.pwd),
            }
        )
        headers = {"Content-Type": "application/json"}
        async with aiohttp.ClientSession() as client:
            resp = await client.post(api, data=body, headers=headers)
        # print(await resp.text())
        _LOGGER.debug(await resp.text())
        if "Set-Cookie" not in resp.headers:
            return "", ""
        self.hjq_token = resp.headers["Set-Cookie"].split("=")[1].split(";")[0]
        self.pass_id = (await resp.json())["data"]["passId"]
        # print("hjq_token:", self.hjq_token, "pass_id", self.pass_id)
        _LOGGER.info(f"hjq_token: {self.hjq_token} pass_id:{self.pass_id}")
        return self.hjq_token, self.pass_id

    async def get_video_auth(self):
        if self.auth:
            return self.auth
        if not self.hjq_token:
            await self.get_hjqtoken_passid()
            return await self.get_video_auth()

        api = "https://video.komect.com/user/login/loginByHJQToken"
        ts = str(int(time.time() * 1000))
        body = {
            "HJQToken": self.hjq_token,
            "nonce": ts + "abcde",
            "passId": self.pass_id,
            "time": ts,
            "userId": self.tel,
        }
        body["sign"] = self.get_video_sign(body, api)
        body = urllib.parse.urlencode(body)
        headers = {
            "AppName": "hejiaqin",
            "DeviceId": "abc",
            "DeviceType": "ANDROID",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        async with aiohttp.ClientSession() as client:
            resp = await client.post(api, data=body, headers=headers)
            _LOGGER.debug(await resp.text())
        self.auth = (await resp.json())["data"]["token"]
        # print(self.tel, "登录成功 video auth:", self.auth)
        _LOGGER.info(f"{self.tel} 登录成功 video auth: {self.auth}")
        return self.auth

    async def get_api_key(self):
        api = "https://andlink.komect.com/espapi/cloud/json/loginByApp?cloudName=CMCC&keyType=0"
        headers = {"API_KEY": self.hjq_token + ":010108:15"}
        async with httpx.AsyncClient(verify=False) as client:
            resp = await client.get(api, headers=headers)
            _LOGGER.debug(await resp.text())
        # print(await resp.json())

    async def get_camera_info(self):
        api = "https://video.komect.com/camera/core/api/bind/queryList"
        ts = str(int(time.time() * 1000))
        params = {
            "nonce": ts + "m5kjt",
            "number": "100",
            "page": "1",
            "time": ts,
            "user_id": self.tel,
        }
        params["sign"] = self.get_video_sign(params, api)
        headers = {
            "AppName": "hejiaqin",
            "DeviceId": "abc",
            "Version": "6.11.1",
            "DeviceType": "ANDROID",
            "AuthorizationToken": self.auth,
        }
        async with aiohttp.ClientSession() as client:
            resp = await client.get(api, params=params, headers=headers)
            _LOGGER.debug(await resp.text())
        if "data" not in await resp.json():
            return None
        if "USER_TOKEN_OUTOFDATE" in (await resp.json())["msg"]:
            _LOGGER.warning("auth 过期！")
            await self.get_video_auth()
            return await self.get_camera_info()
        return (await resp.json())["data"]

    async def get_live_addr(self, base_url, jwt, mac_id):
        api = base_url + "/dcs/device/getLiveAddress"
        ts = str(int(time.time() * 1000))
        params = {
            "macId": mac_id,
            "nonce": ts + "gs08t",
            "requestTime": ts,
            "time": ts,
        }
        params["sign"] = self.get_video_sign(params, api)
        headers = {
            "AppName": "hejiaqin",
            "DeviceId": "abc",
            "Version": "6.11.1",
            "DeviceType": "ANDROID",
            "AuthorizationToken": self.auth,
            "AuthorizationJwtoken": jwt,
        }
        async with aiohttp.ClientSession() as client:
            resp = await client.get(api, params=params, headers=headers)
            _LOGGER.debug(await resp.text())
        # print(resp.text)
        if "data" not in await resp.json():
            return None

        return (await resp.json())["data"]["flv"]

    async def keep_live_addr(self, base_url, jwt, mac_id):
        api = base_url + "/dcs/device/keepOpenLiveAddress"
        ts = str(int(time.time() * 1000))
        params = {
            "macId": mac_id,
            "nonce": ts + "gs08t",
            "time": ts,
        }
        params["sign"] = self.get_video_sign(params, api)
        headers = {
            "AppName": "hejiaqin",
            "DeviceId": "abc",
            "Version": "6.11.1",
            "DeviceType": "ANDROID",
            "AuthorizationToken": self.auth,
            "AuthorizationJwtoken": jwt,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        params = urllib.parse.urlencode(params)
        async with aiohttp.ClientSession() as client:
            resp = await client.post(api, data=params, headers=headers)
            _LOGGER.debug(await resp.text())
        # print("keep_live_addr: ", resp.text)

    async def get_device_info(self, base_url, jwt, mac_id):
        api = base_url + "/dcs/device/fullInfo"
        ts = str(int(time.time() * 1000))
        params = {
            "macId": mac_id,
            "nonce": ts + "gs08t",
            "time": ts,
        }
        params["sign"] = self.get_video_sign(params, api)
        headers = {
            "AppName": "hejiaqin",
            "DeviceId": "abc",
            "Version": "6.11.1",
            "DeviceType": "ANDROID",
            "AuthorizationToken": self.auth,
            "AuthorizationJwtoken": jwt,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        async with aiohttp.ClientSession() as client:
            resp = await client.get(api, params=params, headers=headers)
            # print("keep_live_addr: ", resp.text)
            _LOGGER.debug(await resp.text())
            return (await resp.json())["data"]

    @staticmethod
    def get_md5(value):
        md5_hash = hashlib.md5()
        md5_hash.update(value.encode("utf-8"))
        return md5_hash.hexdigest()

    @staticmethod
    def get_sha1(value):
        sha1_hash = hashlib.sha1()
        sha1_hash.update(value.encode("utf-8"))
        return sha1_hash.hexdigest()

    @staticmethod
    def get_video_sign(body, api):
        secret_key = "r8rw4d1kjwqgqqto9dwsq3ew0ip2np1b"
        s = ""
        for k in sorted(body):
            s += k + body[k]
        path = urllib.parse.urlparse(api).path
        s += path + secret_key
        return HJQApi.get_md5(s)


if __name__ == "__main__":
    api = HJQApi(tel="121", pwd="123@123")
    # asyncio.run(api.main())
