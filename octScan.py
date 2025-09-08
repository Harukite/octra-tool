# 批量读取 wallets 目录下 octra_wallet*.txt 文件，生成 wallet.json

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# 颜色和图标
class Style:
    OK = '\033[32m'  # 绿色
    FAIL = '\033[31m'  # 红色
    INFO = '\033[36m'  # 青色
    WAIT = '\033[33m'  # 黄色
    END = '\033[0m'
    BOLD = '\033[1m'
    ICON_OK = '✅'
    ICON_FAIL = '❌'
    ICON_WAIT = '⏳'
    ICON_INFO = 'ℹ️'
    ICON_NEXT = '➡️'
    ICON_WALLET = '👛'
    ICON_SEND = '🚀'
    ICON_GEN = '🗂'
import requests
import os
import re
import json
import random
import asyncio
from fake_useragent import UserAgent
import time

def fetch_oct_wallets(output_file='multi.txt'):
    """
    从 octrascan.io 获取最新交易中的钱包地址（from/to），去重后写入 output_file。
    """
    url = "https://octrascan.io/"
    headers = {
        "User-Agent": UserAgent().random
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text
        addresses = set(re.findall(r'oct[a-zA-Z0-9]{40,}', html))
        with open(output_file, 'w') as f:
            for addr in addresses:
                f.write(addr + '\n')
        print(f"{Style.OK}{Style.ICON_OK} 已写入 {len(addresses)} 个钱包地址到 {output_file} {Style.END}")
        return list(addresses)
    except Exception as e:
        print(f"{Style.FAIL}{Style.ICON_FAIL} 获取钱包地址失败: {e} {Style.END}")
        return []

def generate_wallet_json(wallets_dir='wallets', output_file='wallet.json'):
    wallets = []
    for fname in os.listdir(wallets_dir):
        if fname.startswith('octra_wallet') and fname.endswith('.txt'):
            fpath = os.path.join(wallets_dir, fname)
            priv, addr = '', ''
            with open(fpath, 'r') as f:
                for line in f:
                    if line.startswith('Private Key (B64):'):
                        priv = line.split(':', 1)[-1].strip()
                    elif line.startswith('Address:'):
                        addr = line.split(':', 1)[-1].strip()
            if priv and addr:
                wallets.append({
                    "priv": priv,
                    "addr": addr,
                    "rpc": "https://octra.network"
                })
    with open(output_file, 'w') as f:
        json.dump(wallets, f, indent=2)
    print(f"{Style.OK}{Style.ICON_GEN} 已生成 {output_file}，共 {len(wallets)} 个钱包 {Style.END}")

# 批量自动转账主流程 - 升级版：每个钱包转账前重新爬取目标，一对多转账
async def auto_multi_send(wallet_file='wallet.json', multi_file_base='multi.txt'):
    """
    增强版批量转账功能：
    1. 每个钱包转账前都重新爬取最新的钱包地址
    2. 每个钱包进行一对多转账（可配置转账次数）
    3. 确保每个钱包转账的目标地址都不一样
    """
    # 动态导入 cli.py 的相关方法和变量
    import importlib
    cli = importlib.import_module('cli')

    # 读取钱包配置
    with open(wallet_file, 'r') as f:
        wallets = json.load(f)
    random.shuffle(wallets)
    print(f"{Style.INFO}{Style.ICON_INFO} 开始增强版批量转账，共 {len(wallets)} 个钱包{Style.END}")
    
    # 用于记录已使用的目标地址，确保不重复
    used_targets = set()
    
    # 遍历每个钱包
    for wallet_idx, w in enumerate(wallets, 1):
        priv = w.get('priv')
        sender_addr = w.get('addr')
        rpc = w.get('rpc', 'https://octra.network')

        print(f"{Style.BOLD}=== 钱包 {wallet_idx}/{len(wallets)}: {sender_addr[:20]}... ==={Style.END}")
        
        # 为当前钱包重新爬取最新目标地址到 multi.txt
        print(f"{Style.INFO}{Style.ICON_WAIT} 为钱包 {wallet_idx} 重新爬取最新目标地址...{Style.END}")
        addresses = fetch_oct_wallets('multi.txt')
        
        if not addresses:
            print(f"{Style.FAIL}{Style.ICON_FAIL} 钱包 {wallet_idx} 无法获取目标地址，跳过{Style.END}")
            continue
        
        # 过滤掉已使用的地址和自己的地址
        available_targets = [addr for addr in addresses if addr not in used_targets and addr != sender_addr]
        
        if not available_targets:
            print(f"{Style.FAIL}{Style.ICON_FAIL} 钱包 {wallet_idx} 没有可用的新目标地址，跳过{Style.END}")
            continue

        # 设置钱包参数
        cli.priv = priv
        cli.addr = sender_addr
        cli.rpc = rpc
        cli.sk = cli.nacl.signing.SigningKey(cli.base64.b64decode(priv)) if priv else None
        cli.pub = cli.base64.b64encode(cli.sk.verify_key.encode()).decode() if cli.sk else None

        # 查询当前钱包余额
        n, b = await cli.st()
        if n is None or b is None:
            print(f"{Style.FAIL}{Style.ICON_FAIL} 钱包 {wallet_idx} 无法获取余额或nonce，跳过{Style.END}")
            continue
            
        print(f"{Style.INFO}钱包 {wallet_idx} 当前余额: {b:.6f} OCT, Nonce: {n}{Style.END}")
        
        # 计算可以进行的转账次数（根据余额决定）
        min_amount = 0.001  # 最小转账金额
        max_amount = 1.0    # 最大转账金额
        max_transfers = min(len(wallets), len(available_targets), int(b / min_amount))  # 最多5笔转账

        if max_transfers == 0:
            print(f"{Style.FAIL}{Style.ICON_FAIL} 钱包 {wallet_idx} 余额不足，跳过{Style.END}")
            continue
        
        print(f"{Style.INFO}钱包 {wallet_idx} 计划进行 {max_transfers} 笔转账{Style.END}")
        
        # 执行多笔转账
        successful_transfers = 0
        current_nonce = n
        
        for transfer_idx in range(max_transfers):
            # 随机选择一个未使用的目标地址
            to_addr = random.choice(available_targets)
            available_targets.remove(to_addr)  # 从可用列表中移除
            used_targets.add(to_addr)  # 添加到已使用列表
            
            # 随机转账金额
            amount = round(round(random.uniform(min_amount, min(max_amount, b * 0.8 / max_transfers)), 6)/100,5)
            
            # 检查余额是否足够
            if b < amount:
                print(f"{Style.FAIL}{Style.ICON_FAIL} 钱包 {wallet_idx} 余额不足，结束转账{Style.END}")
                break
            
            # 构造交易
            current_nonce += 1
            tx, tx_hash = cli.mk(to_addr, amount, current_nonce)
            
            # 随机延迟
            delay = random.uniform(2, 10)
            print(f"{Style.WAIT}{Style.ICON_WAIT} 钱包 {wallet_idx} 转账 {transfer_idx+1}/{max_transfers}: {delay:.1f}秒后转账 {amount} OCT 到 {to_addr[:20]}...{Style.END}")
            await asyncio.sleep(delay)
            
            # 发送交易
            ok, result_hash, dt, result = await cli.snd(tx)
            if ok:
                successful_transfers += 1
                print(f"{Style.OK}{Style.ICON_OK} 钱包 {wallet_idx} 转账 {transfer_idx+1} 成功: {amount} OCT → {to_addr[:20]}... (hash: {result_hash}){Style.END}")
                print(f"{Style.INFO}交易详情: https://octrascan.io/tx/{result_hash}{Style.END}")
                b -= amount  # 更新余额
            else:
                print(f"{Style.FAIL}{Style.ICON_FAIL} 钱包 {wallet_idx} 转账 {transfer_idx+1} 失败: {result_hash}{Style.END}")
                current_nonce -= 1  # 回退nonce
                break
        
        print(f"{Style.INFO}钱包 {wallet_idx} 完成转账: {successful_transfers}/{max_transfers} 笔成功{Style.END}")
        print(f"{Style.INFO}{'-'*60}{Style.END}")
    
    print(f"{Style.BOLD}{Style.ICON_OK} 批量转账完成！总共使用了 {len(used_targets)} 个不同的目标地址{Style.END}")

def query_wallets_info(wallet_file='wallet.json'):
    import importlib
    cli_mod = importlib.import_module('cli')
    with open(wallet_file, 'r') as f:
        wallets = json.load(f)

    results = []
    
    async def query_single_wallet_concurrent(idx, w):
        """并发查询单个钱包，使用独立的session和变量"""
        import aiohttp
        import ssl
        import json
        
        # 创建独立的session
        ssl_context = ssl.create_default_context()
        connector = aiohttp.TCPConnector(ssl=ssl_context, force_close=True)
        session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            connector=connector
        )
        
        priv = w.get('priv')
        addr = w.get('addr')
        rpc = w.get('rpc', 'https://octra.network')
        
        # 初始化结果变量
        balance, nonce, tx_count, enc_balance, total_balance, pending_count = '-', '-', '-', '-', '-', 0
        
        try:
            # 1. 查询基本信息 (余额和nonce) - 使用address端点
            try:
                async with session.get(f"{rpc}/address/{addr}") as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        if text.startswith('{'):
                            data = json.loads(text)
                            balance = float(data.get('balance', 0))
                            nonce = int(data.get('nonce', 0))
                    elif resp.status == 404:
                        balance, nonce = 0, 0
            except:
                pass
            
            # 2. 查询交易历史
            try:
                async with session.get(f"{rpc}/address/{addr}?limit=20") as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        if text.startswith('{'):
                            data = json.loads(text)
                            if data and 'recent_transactions' in data:
                                tx_count = len(data['recent_transactions'])
                            else:
                                tx_count = 0
                    elif resp.status == 404:
                        tx_count = 0
            except:
                pass
            
            # 3. 查询加密余额 (需要私钥授权)
            if priv:
                try:
                    enc_headers = {"X-Private-Key": priv}
                    async with session.get(f"{rpc}/view_encrypted_balance/{addr}", headers=enc_headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            enc_balance = float(data.get("encrypted_balance", "0").split()[0])
                            total_balance = float(data.get("total_balance", "0").split()[0])
                except:
                    pass
            
            # 4. 查询待领取转账
            if priv:
                try:
                    enc_headers = {"X-Private-Key": priv}
                    async with session.get(f"{rpc}/pending_private_transfers?address={addr}", headers=enc_headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            transfers = data.get("pending_transfers", [])
                            pending_count = len(transfers)
                except:
                    pass
            
            # 如果没有加密余额数据，total_balance就是balance
            if total_balance == '-' and balance != '-':
                total_balance = balance
                enc_balance = 0.0
                
        except Exception:
            pass
        finally:
            # 确保关闭session
            await session.close()
        
        return {
            'idx': idx,
            'addr': addr,
            'balance': balance,
            'enc_balance': enc_balance,
            'total_balance': total_balance,
            'nonce': nonce,
            'tx_count': tx_count,
            'pending_count': pending_count
        }
    
    async def query_all_wallets_concurrent():
        """并发查询所有钱包"""
        print(f"{Style.INFO}开始并发查询 {len(wallets)} 个钱包...{Style.END}")
        
        # 创建所有查询任务
        tasks = []
        for idx, w in enumerate(wallets, 1):
            task = query_single_wallet_concurrent(idx, w)
            tasks.append(task)
        
        # 使用 as_completed 来实时显示进度
        results = [None] * len(wallets)
        completed = 0
        
        for coro in asyncio.as_completed(tasks):
            result = await coro
            results[result['idx'] - 1] = result
            completed += 1
            # 实时更新进度
            print(f"\r{Style.INFO}查询进度: {completed}/{len(wallets)} 完成{Style.END}", end='', flush=True)
        
        print()  # 换行
        return results
    
    # 运行并发查询
    import asyncio
    results = asyncio.run(query_all_wallets_concurrent())
    
    # 查询完成后换行
    print()
    
    # 汇总后统一美化输出
    print(f"{Style.BOLD}{Style.ICON_INFO} 钱包汇总信息：{Style.END}")
    header = f"{Style.INFO}序号  地址                                          总余额      Nonce 交易数 进行中{Style.END}"
    print(header)
    print(f"{Style.INFO}{'-'*100}{Style.END}")
    for r in results:
        print(f"{Style.OK}{r['idx']:>2}  {r['addr']:<42} {str(r['total_balance']):>10} {str(r['nonce']):>5} {str(r['tx_count']):>5} {str(r['pending_count']):>6}{Style.END}")
    print(f"{Style.INFO}{'-'*100}{Style.END}")

def function_for_choice_2():
    # 你的函数逻辑
    print("执行函数...")
        # 获取当前事件循环，如果没有则新建
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(auto_multi_send())

if __name__ == '__main__':
    print(f"{Style.BOLD}{Style.ICON_INFO} 请选择功能：{Style.END}")
    print(f"{Style.ICON_NEXT} 1. {Style.ICON_SEND} 批量自动转账")
    print(f"{Style.ICON_NEXT} 2. {Style.ICON_GEN} 生成 wallet.json（从 wallets 目录）")
    print(f"{Style.ICON_NEXT} 3. 💧 一键领水")
    print(f"{Style.ICON_NEXT} 4. 🔍 查询 wallet.json 钱包余额与交易记录")
    choice = input(f"{Style.INFO}请输入序号并回车：{Style.END}").strip()

    if choice == '1':
        # 只创建一次事件循环
        # try:
        #     loop = asyncio.get_event_loop()
        #     if loop.is_closed():
        #         loop = asyncio.new_event_loop()
        #         asyncio.set_event_loop(loop)
        # except RuntimeError:
        #     loop = asyncio.new_event_loop()
        #     asyncio.set_event_loop(loop)
        while True:
            function_for_choice_2()
            loop.run_until_complete(auto_multi_send())
            interval = random.randint(3600, 7200)  # 1到4小时（秒）
            print(f"将在{interval // 60}分钟后重新执行。按Ctrl+C或输入'q'退出。")
            try:
                for _ in range(interval):
                    time.sleep(1)
                    # 检查用户是否想退出（可选：每隔一段时间询问）
            except KeyboardInterrupt:
                print("已退出循环。")
                break
    elif choice == '2':
        generate_wallet_json('wallets', 'wallet.json')
    elif choice == '3':
        import claim_faucet
        claim_faucet.main()
    elif choice == '4':
        query_wallets_info('wallet.json')
    else:
        print(f"{Style.FAIL}{Style.ICON_FAIL} 无效选择，请重新运行。{Style.END}")
