import os
import re

wallet_dir = 'wallets'
addresses = []

print('正在扫描 wallets 目录...')
for filename in os.listdir(wallet_dir):
    if filename.endswith('.txt') and filename.startswith('octra_wallet'):
        filepath = os.path.join(wallet_dir, filename)
        print(f'处理文件: {filename}')
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # 查找 Address: 后面的地址
                match = re.search(r'Address:\s*(oct[a-zA-Z0-9]+)', content)
                if match:
                    address = match.group(1)
                    addresses.append(address)
                    print(f'  找到地址: {address}')
                else:
                    print(f'  未找到地址')
        except Exception as e:
            print(f'  读取文件错误: {e}')

print(f'\n总共找到 {len(addresses)} 个地址')

# 写入到 wallets.txt
with open('wallets.txt', 'w', encoding='utf-8') as f:
    for addr in addresses:
        f.write(addr + '\n')

print(f'地址已保存到 wallets.txt')
print('完成！')
