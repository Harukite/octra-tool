# OCTRA钱包批量管理工具

一个功能强大的OCTRA区块链钱包批量管理和自动化工具集，支持钱包生成、余额查询、批量转账、水龙头领取等功能。

## 🚀 主要功能

### 1. 钱包管理 (`octScan.py`)
- 🔍 **钱包地址爬取**: 从 octrascan.io 获取最新的活跃钱包地址
- 📊 **批量余额查询**: 并发查询多个钱包的余额、交易记录、加密余额等
- 🏗️ **钱包配置生成**: 自动读取 wallets 目录中的钱包文件，生成 wallet.json 配置
- 🚀 **智能批量转账**: 支持一对多转账，自动防重复，实时获取目标地址
- 💧 **一键领水**: 集成水龙头功能，批量领取测试代币

### 2. 交互式钱包客户端 (`cli.py`)
- 💳 **完整钱包功能**: 发送交易、查看余额、交易历史
- 🔒 **隐私功能**: 支持加密/解密余额、隐私转账、领取隐私转账
- 📈 **实时监控**: 实时显示钱包状态、待确认交易、余额变化
- 🔄 **批量操作**: 多笔转账批处理，智能延迟控制
- 📤 **钱包导出**: 支持私钥导出、钱包文件保存等

### 3. 水龙头自动领取 (`claim_faucet.py`)
- 🤖 **自动化领取**: 批量自动领取OCTRA测试代币
- 🧩 **验证码解决**: 集成YesCaptcha API自动解决reCAPTCHA
- 🌐 **代理支持**: 支持代理池轮换，避免IP限制
- ⏰ **智能延迟**: 随机延迟模拟人工操作

## 📦 安装和配置

### 1. 环境要求
- Python 3.7+
- 依赖包: requests, fake-useragent, aiohttp, nacl, cryptography

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置文件设置

#### config.ini 配置
```ini
[YesCaptcha]
api_key=你的YesCaptcha_API密钥

```

#### 代理配置 (proxies.txt)
```
用户名:密码@IP:端口
用户名:密码@IP:端口
# 注释行以#开头
```

#### 钱包地址配置 (wallets.txt)
```
oct6YVYHuFK3Eewrewr23fdsfe6aL1knD7sVi
octCMLeGeR6CqGMyfrewrewrewr23ewr2Jf7w3r
# 每行一个钱包地址
```

## 🎯 使用指南

### 主功能菜单 (`octScan.py`)

运行主程序：
```bash
python3 octScan.py
```

功能选项：
```
1. 👛 爬取钱包地址到 multi.txt
2. 🚀 批量自动转账
3. 🗂 生成 wallet.json（从 wallets 目录）
4. 💧 一键领水
5. 🔍 查询 wallet.json 钱包余额与交易记录
```

### 交互式客户端 (`cli.py`)

运行交互式客户端：
```bash
python3 cli.py
```

需要 `wallet.json` 配置文件：
```json
{
  "priv": "base64编码的私钥",
  "addr": "oct开头的钱包地址", 
  "rpc": "https://octra.network"
}
```

### 水龙头领取 (`claim_faucet.py`)

直接运行或通过主菜单调用：
```bash
python3 claim_faucet.py
```

## 📁 文件结构

```
claim/
├── octScan.py              # 主功能程序
├── cli.py                  # 交互式钱包客户端
├── claim_faucet.py         # 水龙头自动领取
├── config.ini              # 配置文件
├── requirements.txt        # Python依赖
├── wallets.txt            # 钱包地址列表
├── proxies.txt            # 代理服务器列表
├── multi.txt              # 爬取的目标钱包地址
├── wallet.json            # 钱包配置文件
└── wallets/               # 钱包文件目录
    ├── octra_wallet_*.txt # 个人钱包文件
    └── ...
```

## 🔧 核心功能详解

### 1. 智能批量转账

**特点：**
- ✅ 每个钱包转账前重新爬取最新目标地址
- ✅ 确保每个钱包的目标地址不重复
- ✅ 自动计算最优转账次数和金额
- ✅ 支持随机延迟和金额，模拟真实用户行为
- ✅ 实时显示转账进度和结果

**工作流程：**
1. 读取 `wallet.json` 中的钱包配置
2. 为每个钱包重新爬取最新的活跃地址到 `multi.txt`
3. 过滤掉已使用的地址和自己的地址
4. 根据余额计算可转账次数（最多与钱包数量相等）
5. 随机选择目标地址和转账金额
6. 串行执行转账，每笔间隔2-10秒

### 2. 并发余额查询

**特点：**
- ⚡ 异步并发查询，大幅提升速度
- 📊 查询公开余额、加密余额、交易计数
- 🔒 支持私钥授权查询隐私信息
- 📋 美化表格输出，信息一目了然

**查询信息：**
- 公开余额 (Public Balance)
- 加密余额 (Encrypted Balance)  
- 总余额 (Total Balance)
- Nonce 值
- 交易数量
- 待领取转账数量

### 3. 水龙头自动化

**特点：**
- 🤖 全自动化流程，无需人工干预
- 🧩 自动解决reCAPTCHA验证码
- 🌐 支持代理池，避免IP限制
- ⏰ 智能延迟，防止被反机器人检测

**工作原理：**
1. 从 `wallets.txt` 读取钱包地址列表
2. 为每个钱包分配对应的代理（如果可用）
3. 调用YesCaptcha API解决reCAPTCHA
4. 提交领水请求到 faucet.octra.network
5. 随机延迟后处理下一个钱包

## ⚙️ 高级配置

### 转账参数调整

在 `octScan.py` 的 `auto_multi_send` 函数中可调整：

```python
min_amount = 0.001    # 最小转账金额
max_amount = 1.0      # 最大转账金额
max_transfers = len(wallets)  # 每个钱包最大转账次数
delay_range = (2, 10) # 转账间隔延迟范围（秒）
```

### 查询超时设置

在相关函数中可调整HTTP请求超时：

```python
timeout=aiohttp.ClientTimeout(total=10)  # 10秒超时
```

### 代理轮换策略

目前使用钱包索引对应代理索引的策略，可根据需要修改为随机选择：

```python
def get_random_proxy():
    return random.choice(all_proxies) if all_proxies else None
```

## 🛡️ 安全注意事项

### 1. 私钥安全
- ⚠️ **绝不要在生产环境使用真实私钥**
- 🔒 钱包文件自动设置为只读权限 (chmod 600)
- 🚫 避免在公共网络或不安全环境中运行

### 2. 代理使用
- 🌐 建议使用付费代理服务确保稳定性
- 🔄 定期更换代理避免被封
- 📊 监控代理使用情况和成功率

### 3. API密钥
- 🔑 妥善保管 [YesCaptcha](https://yescaptcha.com/i/H27VrR) API密钥
- 💰 监控API使用量和余额
- 🚫 不要将config.ini文件提交到版本控制

## 🐛 故障排除

### 常见问题

**1. 转账失败 "insufficient balance"**
- 检查钱包余额是否足够
- 确认转账金额设置合理
- 查看是否有待确认交易占用余额

**2. 水龙头领取失败**
- 检查 [YesCaptcha](https://yescaptcha.com/i/H27VrR) API密钥是否正确
- 确认代理连接是否正常
- 查看是否超过了水龙头限制（24小时内只能领取一次）

**3. 钱包地址爬取失败**
- 检查网络连接是否正常
- 确认octrascan.io网站是否可访问
- 尝试更换User-Agent或使用代理

**4. 并发查询超时**
- 降低并发数量
- 增加超时时间
- 检查RPC节点是否稳定

### 调试模式

在代码开头添加调试日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 性能优化

### 1. 并发优化
- 使用asyncio异步处理，提升I/O密集型操作效率
- 合理控制并发数量，避免对服务器造成压力
- 使用连接池复用HTTP连接

### 2. 内存优化  
- 及时关闭HTTP会话和连接
- 限制交易历史记录数量
- 使用生成器处理大量数据

### 3. 网络优化
- 实现请求重试机制
- 使用合适的超时设置
- 支持代理池轮换

## 🔄 更新日志

### v1.3.0 (2025-08-25)
- ✅ 优化批量转账逻辑，不再创建多个multi_wallet文件
- ✅ 改进为直接更新multi.txt文件内容
- ✅ 修复转账金额计算问题（除以100降低金额）
- ✅ 增强错误处理和日志输出

### v1.2.0 
- ✅ 新增并发余额查询功能
- ✅ 支持隐私转账和加密余额查询
- ✅ 优化转账成功率和稳定性

### v1.1.0
- ✅ 集成水龙头自动领取功能
- ✅ 支持代理池和验证码自动解决
- ✅ 改进用户界面和日志输出

### v1.0.0
- ✅ 基础钱包管理功能
- ✅ 批量转账和地址爬取
- ✅ 交互式钱包客户端

## 💡 使用技巧

### 1. 钱包文件格式
钱包文件应包含以下信息：
```
OCTRA WALLET
==================================================
Private Key (B64): XGxLGXYdNM16rRiX8jyfswfrewrzQrst+55b9yZEUw=
Address: oct6YVYHuFK3Erdsfewrgdstewdfsgdsfds
```

### 2. 最佳实践
- 在批量转账前先查询所有钱包余额
- 使用功能1爬取最新的活跃钱包地址
- 定期备份重要的钱包文件
- 监控转账结果和交易状态

### 3. 错误处理
- 程序会自动跳过余额不足的钱包
- 网络错误时会显示详细的错误信息
- 转账失败时会自动回退nonce值

## 📝 许可证

本项目仅供学习和测试使用，请勿用于任何非法用途。使用本工具产生的任何后果由使用者自行承担。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

---

**⚠️ 免责声明**: 本工具仅用于OCTRA测试网络，请勿在主网环境中使用。使用前请确保理解相关风险。
