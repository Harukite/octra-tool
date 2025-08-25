import os
import json
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
    print(f"已生成 {output_file}，共 {len(wallets)} 个钱包")

generate_wallet_json()
