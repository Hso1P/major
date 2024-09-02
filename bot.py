import sys
import random
import requests
import urllib.parse
import json
from colorama import *
from src.headers import headers
from src.auth import get_token
from src.utils import log, log_line, countdown_timer, mrh, pth, kng, hju, bru, _banner, _clear

init(autoreset=True)

class Major:
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.auto_do_task = config.get('auto_complete_task', False)
        self.auto_play_hold_coin = config.get('auto_play_hold_coin', False)
        self.auto_spin = config.get('auto_spin_roulete', False)
        self.account_delay = config.get('account_delay', 5)
        self.wait_time = config.get('wait_time', 3600)
        self.data_file = config.get('data_file', 'data.txt')
        self.use_proxies = config.get('use_proxies', False)
        self.proxies = self.load_proxies(config.get('proxy_file', 'proxies.txt'))

    def load_proxies(self, file_path):
        proxies = []
        with open(file_path, 'r') as f:
            for line in f:
                proxies.append(line.strip())
        return proxies

    def get_proxy(self):
        if self.use_proxies and self.proxies:
            return random.choice(self.proxies)
        return None

    def request(self, method, url, token=None, payload=None):
        proxy = self.get_proxy()
        proxies = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        } if proxy else None
        try:
            response = requests.request(method, url, headers=headers(token=token), json=payload, proxies=proxies, timeout=20)
            return response.json() if response.status_code == 200 else None
        except requests.RequestException as e:
            log(f"Request Exception: {e}")
            return None


    def check_in(self, token):
        url = "https://major.glados.app/api/user-visits/visit/"
        result = self.request("POST", url, token)
        return result.get("is_increased", False) if result else False

    def get_task(self, token, task_type):
        url = f"https://major.glados.app/api/tasks/?is_daily={task_type}"
        result = self.request("GET", url, token)
        return result if result else []

    def do_task(self, token, task_id):
        url = "https://major.glados.app/api/tasks/"
        payload = {"task_id": task_id}
        result = self.request("POST", url, token, payload)
        return result.get("is_completed", False) if result else False

    def get_streak(self, token):
        url = "https://major.glados.app/api/user-visits/streak/"
        result = self.request("GET", url, token)
        if result:
            streak = result.get("streak", 0)
            log(f"{hju}Current Streak: {pth}{streak}")
            return streak
        else:
            log(f"{mrh}Failed to get streak information")
            return None

    def get_position(self, user_id, token):
        url = f"https://major.glados.app/api/users/top/position/{user_id}/"
        result = self.request("GET", url, token)
        if result:
            position = result.get("position", "Unknown")
            log(f"{hju}Position: {pth}{position:,}")
            return position
        else:
            log(f"{mrh}Failed to get position information")
            return None

    def get_tele_id_from_query(self, query):
        user_data_encoded = urllib.parse.parse_qs(query).get('user', [None])[0]
        return json.loads(urllib.parse.unquote(user_data_encoded)).get('id') if user_data_encoded else None

    def userinfo(self, token, tele_id):
        url = f"https://major.glados.app/api/users/{tele_id}/"
        data = self.request("GET", url, token)
        if data:
            log(f"{hju}Username: {pth}{data.get('username')}")
            log(f"{hju}Balance: {pth}{data.get('rating', 0):,}")
        return data

    def hold_coin(self, token, coins):
        url = "https://major.glados.app/api/bonuses/coins/"
        payload = {"coins": coins}
        result = self.request("POST", url, token, payload)
        return result.get("success", False) if result else False

    def spin(self, token):
        url = "https://major.glados.app/api/roulette"
        result = self.request("POST", url, token)
        return result.get("rating_award", 0) if result else 0

    def process_account(self, account):
        token = get_token(data=account)
        query = account  

        if not token:
            log(f"{mrh}Token not found! Please get a new query ID.")
            return
    

        tele_id = self.get_tele_id_from_query(query)
        if tele_id:
            self.userinfo(token, tele_id)
            self.get_position(tele_id, token)  
        
        self.get_streak(token)
        
        if self.check_in(token):
            log(f"{hju}Checkin Successfully")
        else:
            log(f"{bru}Already Checkin Today")

        if self.auto_do_task:
            for task_type in ["true", "false"]:
                tasks = self.get_task(token, task_type)
                for task in tasks:
                    task_name = task.get("title", "Unknown Task").replace("\n", "")
                    if self.do_task(token, task.get("id", "")):
                        log(f"{pth}{task_name}: {hju}Completed")
                    else:
                        log(f"{pth}{task_name}: {mrh}Incomplete")

        if self.auto_play_hold_coin:
            coins = random.randint(800, 900)
            if self.hold_coin(token, coins):
                log(f"{hju}Success Hold Coin | Reward {pth}{coins} {kng}Coins")
            else:
                log(f"{kng}Can't Play Hold Coin, invite or waiting!")

        if self.auto_spin:
            points = self.spin(token)
            if points:
                log(f"{hju}Spin Success | Reward {pth}{points:,} {kng}points")
            else:
                log(f"{kng}Can't spin, invite or waiting!")

    def main(self):
        while True:
            _clear()
            _banner()
            log_line()
            with open(self.data_file, "r") as f:
                accounts = f.read().splitlines()

            log(f"{hju}Number of accounts: {pth}{len(accounts)}")
            log(f"{hju}Use Proxies: {pth}{self.use_proxies}")
            log_line()

            for idx, account in enumerate(accounts):
                log(f"{hju}Account: {pth}{idx + 1}/{len(accounts)}")

                try:
                    self.process_account(account)
                    log_line()
                    countdown_timer(self.account_delay)
                except Exception as e:
                    log(f"{mrh}Error: {pth}{e}")

            countdown_timer(self.wait_time)

if __name__ == "__main__":
    try:
        major = Major()
        major.main()
    except KeyboardInterrupt:
        sys.exit()
