# Control4Computer

一个用手机网页远程控制电脑输入的小工具。启动后，手机和电脑处在同一个局域网内时，可以在手机浏览器中触发常用按键、移动鼠标并点击鼠标左右键。

## 功能

- 支持按键：`space`、`enter`、`esc`、`up`、`down`、`left`、`right`
- 支持方向键和空格键长按连续触发
- 支持手机触摸板滑动移动电脑鼠标
- 支持鼠标左键、右键点击
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

### 双击启动

在项目目录中双击：

```text
PCRun.bat
```

它会在后台启动服务，不会保留控制台窗口。如果项目目录下存在 `.venv` 虚拟环境，会优先使用 `.venv\Scripts\pythonw.exe`；否则依次尝试系统 `pyw`、`pythonw`、`python`。

双击启动后，可以在浏览器打开：

```text
http://127.0.0.1:8000/
```

页面会显示本次启动生成的 token 链接，点击后进入控制页面。

### 命令行启动

也可以手动运行：

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
5. 在页面上使用控制区：
   - 九宫格按键区左上角是 `ESC`，右上角是 `SPACE`，中间是 `ENTER`。
   - 点击或长按方向键、空格键控制电脑。
   - 点击 `ENTER` 或 `ESC` 触发对应按键。
   - 页面上方的大块触摸板区域支持全屏式操作，滑动可移动鼠标。
   - 在触摸板区域轻触一次触发鼠标左键单击，快速轻触两次触发鼠标左键双击。
   - 在触摸板区域长按触发鼠标右键点击。

## 停止

### 双击停止

在项目目录中双击：

```text
PCStop.bat
```

它会通过 PowerShell 停止正在运行的 `remote_keys.py` Python/Pythonw 进程。

### 命令行停止

如果是手动用命令行启动的，也可以回到运行 `python remote_keys.py` 的终端，按：

```text
Ctrl+C
```

服务停止后，手机页面将无法继续控制电脑。下次重新启动时会生成新的 token。

## 注意事项

- 只建议在可信局域网内使用。
- 启动期间，拥有 token 链接的人可以触发电脑按键。
- 如果手机无法访问，请检查电脑和手机是否在同一网络，以及防火墙是否放行 `8000` 端口。
