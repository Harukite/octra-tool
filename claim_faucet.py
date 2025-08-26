import random
import requests
import time
import json
import configparser
from fake_useragent import UserAgent
# 读取配置文件
config = configparser.ConfigParser()
config.read('config.ini')

# YesCaptcha API 配置
YESCAPTCHA_API_KEY = config['YesCaptcha']['api_key']
YESCAPTCHA_CREATE_TASK_URL = "https://api.yescaptcha.com/createTask"
YESCAPTCHA_GET_TASK_RESULT_URL = "https://api.yescaptcha.com/getTaskResult"

# 领水网站配置
FAUCET_URL = "https://faucet.octra.network/"
RECAPTCHA_SITEKEY = "6LekoXkrAAAAAMlLCpc2KJqSeUHye6KMxOL5_SES"

# 代理池配置：从 proxies.txt 读取所有代理，每次请求随机选一个

def load_proxies():
    proxies_list = []
    try:
        with open('proxies.txt', 'r') as f:
            for line in f:
                proxy = line.strip()
                if proxy and not proxy.startswith('#'):
                    # 格式：用户名:密码@IP:端口
                    proxies_list.append(proxy)
    except FileNotFoundError:
        print("proxies.txt 文件未找到，将不使用代理。")
    return proxies_list

all_proxies = load_proxies()

# 获取与钱包地址顺序对应的代理

def get_proxy_by_index(idx):
    if not all_proxies or idx >= len(all_proxies):
        return None
    proxy_str = all_proxies[idx]
    proxy_url = f"http://{proxy_str}" if not proxy_str.startswith("http") else proxy_str
    return {
        "http": proxy_url,
        "https": proxy_url,
    }

# 颜色定义
class LogColor:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def solve_recaptcha_v2(sitekey, pageurl, proxy=None, address=None, proxy_info=None):
    """使用YesCaptcha解决reCAPTCHA v2"""
    task_payload = {
        "clientKey": YESCAPTCHA_API_KEY,
        "task": {
            "type": "NoCaptchaTaskProxyless",
            "websiteURL": pageurl,
            "websiteKey": sitekey
        }
    }
    try:
        response = requests.post(YESCAPTCHA_CREATE_TASK_URL, json=task_payload, proxies=proxy)
        response.raise_for_status()
        task_id = response.json().get("taskId")
        if not task_id:
            print(f"{LogColor.FAIL}[钱包:{address}][代理:{proxy_info}] 创建任务失败: {response.json()}{LogColor.ENDC}")
            return None
        # 轮询获取结果
        for _ in range(30):
            time.sleep(10)
            result_payload = {
                "clientKey": YESCAPTCHA_API_KEY,
                "taskId": task_id
            }
            result_response = requests.post(YESCAPTCHA_GET_TASK_RESULT_URL, json=result_payload, proxies=proxy)
            result_response.raise_for_status()
            result_data = result_response.json()
            if result_data.get("status") == "ready":
                g_recaptcha_response = result_data["solution"]["gRecaptchaResponse"]
                return g_recaptcha_response
            elif result_data.get("status") != "processing":
                print(f"{LogColor.FAIL}[钱包:{address}][代理:{proxy_info}] 获取reCAPTCHA结果失败: {result_data}{LogColor.ENDC}")
                return None
        print(f"{LogColor.WARNING}[钱包:{address}][代理:{proxy_info}] 等待reCAPTCHA结果超时。{LogColor.ENDC}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"{LogColor.FAIL}[钱包:{address}][代理:{proxy_info}] 请求YesCaptcha API时发生错误: {e}{LogColor.ENDC}")
        return None

def claim_faucet(address, recaptcha_token, proxy=None, proxy_info=None):
    """向领水网站提交请求"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Origin": "https://faucet.octra.network",
        "Referer": "https://faucet.octra.network/",
        "User-Agent": UserAgent().random
    }
    payload = {
        "address": (None, address),
        "g-recaptcha-response": (None, recaptcha_token),
        "is_validator": (None, "false")
    }
    try:
        response = requests.post(FAUCET_URL + "claim", files=payload, proxies=proxy)
        response.raise_for_status()
        
        # 打印返回的状态码和内容
        print(f"{LogColor.OKCYAN}[钱包:{address}][代理:{proxy_info}] 响应状态码: {response.status_code}{LogColor.ENDC}")
        print(f"{LogColor.OKCYAN}[钱包:{address}][代理:{proxy_info}] 响应内容: {response.text}{LogColor.ENDC}")
        
        # 尝试解析JSON响应
        try:
            json_response = response.json()
            print(f"{LogColor.OKCYAN}[钱包:{address}][代理:{proxy_info}] JSON响应: {json.dumps(json_response, indent=2, ensure_ascii=False)}{LogColor.ENDC}")
        except json.JSONDecodeError:
            print(f"{LogColor.WARNING}[钱包:{address}][代理:{proxy_info}] 响应不是JSON格式{LogColor.ENDC}")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"{LogColor.FAIL}[钱包:{address}][代理:{proxy_info}] 提交领水请求时发生错误: {e}{LogColor.ENDC}")
        if 'response' in locals() and response and response.text:
            print(f"{LogColor.FAIL}[钱包:{address}][代理:{proxy_info}] 错误响应内容: {response.text}{LogColor.ENDC}")
        return False

def main():
    # 从wallets.txt读取钱包地址
    try:
        with open('wallets.txt', 'r') as f:
            wallet_addresses = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("wallets.txt文件未找到，请创建并添加钱包地址。")
        return

    if not wallet_addresses:
        print("wallets.txt中没有找到钱包地址，请添加。")
        return

    print(f"将处理以下钱包地址: {wallet_addresses}")

    for idx, address in enumerate(wallet_addresses):
        proxy = get_proxy_by_index(idx)
        proxy_info = proxy['http'] if proxy else '无代理'
        print(f"\n{LogColor.HEADER}[钱包:{address}][代理:{proxy_info}] 开始处理{LogColor.ENDC}")
        delay = random.randint(3, 13)
        time.sleep(delay)
        print(f"\n{LogColor.HEADER}[等待⌛️{delay}秒] 开始处理{LogColor.ENDC}")
        recaptcha_token = solve_recaptcha_v2(RECAPTCHA_SITEKEY, FAUCET_URL, proxy, address, proxy_info)
        if recaptcha_token:
            claim_faucet(address, recaptcha_token, proxy, proxy_info)
            print(f"{LogColor.OKGREEN}[钱包:{address}][代理:{proxy_info}] 处理结束（成功）{LogColor.ENDC}")
        else:
            print(f"{LogColor.FAIL}[钱包:{address}][代理:{proxy_info}] 处理结束（失败，reCAPTCHA未解决）{LogColor.ENDC}")
        time.sleep(random.randint(1, 10))

if __name__ == "__main__":
    main()


