# Control4Computer

一个用手机网页远程触发电脑按键的小工具。启动后，手机和电脑处在同一个局域网内时，可以在手机浏览器中点击方向键和空格键，电脑会收到对应按键输入。

## 功能

- 支持按键：`space`、`up`、`down`、`left`、`right`
- 支持点按和长按连续触发
- 每次启动都会生成临时 token，避免没有 token 的请求直接控制电脑

## 环境要求

- Python 3
- 手机和电脑连接到同一个局域网
- 电脑防火墙允许访问本机的 `8000` 端口

## 安装依赖

建议先创建虚拟环境：

```bash
python -m venv .venv
source .venv/Scripts/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 启动

运行：

```bash
python remote_keys.py
```

启动成功后，终端会显示类似信息：

```text
Remote Keys is running.
Open on this computer: http://127.0.0.1:8000/?token=xxxx
Open on your phone: http://<computer-lan-ip>:8000/ then tap the token link
```

## 在本机使用

在电脑浏览器打开终端里显示的本机地址：

```text
http://127.0.0.1:8000/?token=xxxx
```

其中 `xxxx` 是本次启动生成的 token。

## 在手机上使用

1. 确认手机和电脑在同一个局域网。
2. 查看电脑的局域网 IP。
   - Windows 可以运行：

     ```bash
     ipconfig
     ```

   - 找到当前网络适配器里的 IPv4 地址，例如 `192.168.1.23`。
3. 在手机浏览器打开：

   ```text
   http://电脑局域网IP:8000/
   ```

   例如：

   ```text
   http://192.168.1.23:8000/
   ```

4. 页面会显示带 token 的控制页面链接，点击该链接进入控制页面。
5. 点击或长按页面上的方向键、空格键即可控制电脑。

## 停止

回到运行 `python remote_keys.py` 的终端，按：

```text
Ctrl+C
```

服务停止后，手机页面将无法继续控制电脑。下次重新启动时会生成新的 token。

## 注意事项

- 只建议在可信局域网内使用。
- 启动期间，拥有 token 链接的人可以触发电脑按键。
- 如果手机无法访问，请检查电脑和手机是否在同一网络，以及防火墙是否放行 `8000` 端口。
