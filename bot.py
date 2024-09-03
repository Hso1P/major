import sys
import random
import requests
import urllib.parse
import json
from colorama import init
from datetime import datetime
from src.headers import headers
from src.auth import get_token
from src.utils import log, log_line, countdown_timer, _banner, _clear, mrh, hju, kng, pth, bru, htm, reset

init(autoreset=True)

class Major:
    def __init__(self, config_file='config.json'):
        with open(config_file, 'r') as f:
            config = json.load(f)
        self.auto_do_task = config.get('auto_complete_task', False)
        self.auto_play_hold_coin = config.get('auto_play_hold_coin', False)
        self.auto_spin = config.get('auto_spin_roulete', False)
        self.wait_time = config.get('wait_time', 3600)
        self.account_delay = config.get('account_delay', 5)
        self.data_file = config.get('data_file', 'data.txt')
        self.proxies = self.load_proxies('proxies.txt')

    def load_proxies(self, file_name):
        try:
            with open(file_name, 'r') as f:
                proxy_list = f.read().splitlines()
                proxies = []
                for proxy in proxy_list:
                    proxies.append({
                        'http': f'http://{proxy}',
                        'https': f'https://{proxy}'
                    })
                return proxies
        except Exception as e:
            log(f"Error loading proxies: {e}")
            return []

    def request(self, method, url, token, proxies=None, json=None):
        try:
            response = requests.request(
                method, url, headers=headers(token=token), proxies=proxies, json=json, timeout=20
            )
            return response.json()
        except requests.exceptions.RequestException as e:
            return None
        
    def check_in(self, token, proxies=None):
        url = "https://major.glados.app/api/user-visits/visit/"
        result = self.request("POST", url, token, proxies=proxies)
        if result:
            return result.get("is_increased", False)
        return False

    def get_task(self, token, task_type, proxies=None):
        url = f"https://major.glados.app/api/tasks/?is_daily={task_type}"
        return self.request("GET", url, token, proxies=proxies)

    def do_task(self, token, task_id, proxies=None):
        url = "https://major.glados.app/api/tasks/"
        payload = {"task_id": task_id}
        result = self.request("POST", url, token, proxies=proxies, json=payload)
        if result:
            return result.get("is_completed", False)
        return False

    def get_tele_id_from_query(self, query):
        user_data_encoded = urllib.parse.parse_qs(query).get('user', [None])[0]
        if user_data_encoded:
            user_data = json.loads(urllib.parse.unquote(user_data_encoded))
            return user_data.get('id') 
        return None

    def userinfo(self, token, tele_id, proxies=None):
        url = f"https://major.glados.app/api/users/{tele_id}/"
        data = self.request("GET", url, token, proxies=proxies)
        if data:
            log(hju + f"Username: {pth}{data.get('username', None)}")
            log(hju + f"Balance: {pth}{data.get('rating', 0):,}")
            return data
        log(f"{mrh}Failed to fetch user info")
        return None

    def hold_coin(self, token, coins, proxies=None):
        url = "https://major.glados.app/api/bonuses/coins/"
        payload = {"coins": coins}
        data = self.request("POST", url, token, proxies=proxies, json=payload)
        
        if data:
            if data.get("success", False):
                return True

            detail = data.get("detail", {})
            blocked_until = detail.get("blocked_until")
            
            if blocked_until is not None:
                blocked_until_time = datetime.fromtimestamp(blocked_until).strftime('%Y-%m-%d %H:%M:%S')
                log(hju + f"Hold Coin blocked until: {pth}{blocked_until_time}")
            
        return False

    def spin(self, token, proxies=None):
        url = "https://major.glados.app/api/roulette"
        data = self.request("POST", url, token, proxies=proxies)
        
        if data:
            detail = data.get("detail", {})
            blocked_until = detail.get("blocked_until")
            
            if blocked_until is not None:
                blocked_until_time = datetime.fromtimestamp(blocked_until).strftime('%Y-%m-%d %H:%M:%S')
                log(hju + f"Spin blocked until: {pth}{blocked_until_time}")
            
            return data.get("rating_award", 0)
        
        return 0
    
    def squad(self, token, squad_id, proxies=None):
        url = f"https://major.glados.app/api/squads/{squad_id}/join/"
        response = self.request("POST", url, token, proxies=proxies)
        if response.get("status") == "ok":
            return True
        else:
            return False

    def get_streak(self, token, proxies=None):
        url = "https://major.glados.app/api/user-visits/streak/"
        result = self.request("GET", url, token, proxies=proxies)
        if result:
            streak = result.get("streak", 0)
            log(f"{hju}Current Streak: {pth}{streak}")
            return streak
        log(f"{mrh}Failed to get streak information")
        return None

    def get_position(self, user_id, token, proxies=None):
        url = f"https://major.glados.app/api/users/top/position/{user_id}/"
        result = self.request("GET", url, token, proxies=proxies)
        if result:
            position = result.get("position", "Unknown")
            log(f"{hju}Position: {pth}{position:,}")
            return position
        log(f"{mrh}Failed to get position information")
        return None

    def main(self):
        while True:
            _clear()
            _banner()
            with open(self.data_file, "r") as f:
                accounts = f.read().splitlines()

            log(hju + f"Number of accounts: {bru}{len(accounts)}")
            log_line()

            for idx, account in enumerate(accounts):
                log(hju + f"Account: {bru}{idx + 1}/{len(accounts)}")

                try:
                    token = get_token(data=account)
                    query = account
                    
                    if token:
                        tele_id = self.get_tele_id_from_query(query)
                        if tele_id:
                            squad_id = "1408216150"
                            self.squad(token, squad_id)
                            self.userinfo(token, tele_id)
                            self.get_position(tele_id, token)
                            self.get_streak(token)
                        self.check_in(token)
                        
                        if self.auto_do_task:
                            tasks = self.get_task(token, "true") + self.get_task(token, "false")
                            for task in tasks:
                                task_name = task.get("title", "").replace("\n", "")
                                completed = self.do_task(token, task.get("id", ""))
                                log(f"{f'{hju}Completed' if completed else f'{mrh}Incomplete'} {pth}{task_name}")
                        if self.auto_play_hold_coin:
                            coins = random.randint(800, 900)
                            success = self.hold_coin(token, coins)
                            if success:
                                log(hju + f"Success Hold Coin | Reward {pth}{coins} {hju}Coins")
                        if self.auto_spin:
                            points = self.spin(token)
                            if points:
                                log(hju + f"Spin Success | Reward {pth}{points:,} {hju}points")
                        
                        log_line()
                    else:
                        log(mrh + f"Error fetching token, please try again!")
                except Exception as e:
                    log(mrh + f"Error: {kng}{e}")
                countdown_timer(self.account_delay)
            countdown_timer(self.wait_time)

if __name__ == "__main__":
    try:
        major = Major()
        major.main()
    except KeyboardInterrupt:
        sys.exit()
