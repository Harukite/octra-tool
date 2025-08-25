# Octra Faucet 自动领水脚本

## 功能简介
- 批量为钱包地址自动领取 Octra 测试币。
- 自动解决 reCAPTCHA 验证。
- 支持代理池，代理与钱包顺序一一对应。
- 每次请求前有 3~13 秒随机延迟，模拟人工操作。
- 日志输出带有彩色区分，便于快速识别处理进度和异常。

## 使用方法
1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 配置 `config.ini`，填写 YesCaptcha API key。
3. 在 `wallets.txt` 中添加钱包地址，每行一个。
4. 在 `proxies.txt` 中添加代理，每行一个，格式为：
   ```
   用户名:密码@IP:端口
   # 示例：9cfa75dd:3rIidRO0@156.250.117.221:25975
   ```
   - 钱包地址与代理顺序一一对应，钱包数量建议与代理数量一致。
5. 运行脚本：
   ```bash
   python claim_faucet.py
   ```

## 日志说明
- 日志每条均带有钱包地址和代理信息。
- 主要只打印每个钱包的“开始处理”和“处理结束”信息。
- 错误和异常信息会高亮显示。

## 注意事项
- 需注册 [YesCaptcha](https://yescaptcha.com/i/H27VrR) 并获取 API key.
- 建议使用代理，避免 IP 被限制。
- 代理数量不足时，后续钱包将不使用代理。
- 支持彩色日志输出，建议在支持 ANSI 颜色的终端运行。

## 依赖
- requests
- configparser
- fake_useragent
