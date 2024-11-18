import os
import uuid
import json
import aiohttp
import argparse
from datetime import datetime, timezone

import requests
from fake_useragent import UserAgent
from colorama import *

green = Fore.LIGHTGREEN_EX
red = Fore.LIGHTRED_EX
magenta = Fore.LIGHTMAGENTA_EX
white = Fore.LIGHTWHITE_EX
black = Fore.LIGHTBLACK_EX
reset = Style.RESET_ALL
yellow = Fore.LIGHTYELLOW_EX


class Grass:
    def __init__(self, config):
        # userName = config["user"]
        # password = config["password"]
        self.proxy = config["proxy"]
        self.ua = config["ua"]
        # self.userid = self.get_uid(userName,password,self.ua,self.proxy)
        self.userid = config["uid"]
        # if self.userid == False:
        #     print("{} 获取不到userid".format(userName))
        #     exit()
        self.ses = aiohttp.ClientSession()


    def get_uid(self,username,password,ua,socks5):
        print(username,password,ua,socks5)
        url = "https://api.getgrass.io/login"
        headers ={
            "Accept": "*/*",
            "Accept-Language": "en",
            "User-Agent":ua,
            "Content-Type": "application/json"
        }
        proxy = {
            "http":socks5,
            "https":socks5
        }
        data = {"username":username,"password":password}
        try:
            resp = requests.post(url,headers,json=data,timeout=10,proxies=proxy)
            print(resp.text)
            return resp.json()["result"]["data"]["userId"]
        except:
            return False

    def log(self, msg):
        now = datetime.now(tz=timezone.utc).isoformat(" ").split(".")[0]
        print(f"{black}[{now}] {reset}{msg}{reset}")

    @staticmethod
    async def ipinfo(proxy=None):
        async with aiohttp.ClientSession() as client:
            result = await client.get("https://api.ipify.org/", proxy=proxy)
            return await result.text()

    async def start(self):
        max_retry = 10
        retry = 1
        proxy = self.proxy
        if proxy is None:
            proxy = await Grass.ipinfo()
        browser_id = uuid.uuid5(uuid.NAMESPACE_URL, proxy)
        # useragent = UserAgent().random
        headers = {
            "Host": "proxy2.wynd.network:4444",
            "Connection": "Upgrade",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": self.ua,
            "Upgrade": "websocket",
            "Origin": "chrome-extension://lkbnfiajjmbhnfledhphioinpickokdi",
            "Sec-WebSocket-Version": "13",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        }
        while True:
            try:
                # if retry >= max_retry:
                #     self.log(f"{yellow}max retrying reacted, skip the proxy !")
                #     await self.ses.close()
                #     return
                async with self.ses.ws_connect(
                    "wss://proxy2.wynd.network:4444",
                    headers=headers,
                    proxy=self.proxy,
                    timeout=1000,
                    autoclose=False,
                ) as wss:
                    res = await wss.receive_json()
                    auth_id = res.get("id")
                    if auth_id is None:
                        self.log(f"{red}auth id is None")
                        return None
                    auth_data = {
                        "id": auth_id,
                        "origin_action": "AUTH",
                        "result": {
                            "browser_id": browser_id.__str__(),
                            "user_id": self.userid,
                            "user_agent": self.ua,
                            "timestamp": int(datetime.now().timestamp()),
                            "device_type": "extension",
                            "version": "4.26.2",
                            "extension_id": "lkbnfiajjmbhnfledhphioinpickokdi",
                        },
                    }
                    await wss.send_json(auth_data)
                    self.log(f"{green}成功连接 {white}到服务器!")
                    retry = 1
                    while True:
                        ping_data = {
                            "id": uuid.uuid4().__str__(),
                            "version": "1.0.0",
                            "action": "PING",
                            "data": {},
                        }
                        await wss.send_json(ping_data)
                        self.log(f"{white}发送 {green}ping {white}到服务器 !")
                        pong_data = {"id": "F3X", "origin_action": "PONG"}
                        await wss.send_json(pong_data)
                        self.log(f"{white}发送 {magenta}pong {white}到服务器 !")
                        # you can edit the countdown in code below
                        await countdown(3)
            except KeyboardInterrupt:
                await self.ses.close()
                exit()
            except Exception as e:
                self.log(f"{red}error : {white}{e}")
                retry += 1
                continue


async def countdown(t):
    for i in range(t, 0, -1):
        minute, seconds = divmod(i, 60)
        hour, minute = divmod(minute, 60)
        seconds = str(seconds).zfill(2)
        minute = str(minute).zfill(2)
        hour = str(hour).zfill(2)
        print(f"waiting for {hour}:{minute}:{seconds} ", flush=True, end="\r")
        await asyncio.sleep(1)


async def main(configs):
    tasks = [Grass(config).start() for config in configs]
    await asyncio.gather(*tasks)


def read_config():
    import yaml
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)["USERS"]
            return config
    except FileNotFoundError:
        print("YAML 文件未找到，请检查路径。")
        exit()

if __name__ == "__main__":
    # print(read_config())
    # exit()
    try:
        import asyncio
        asyncio.run(main(read_config()))
    except KeyboardInterrupt:
        exit()
