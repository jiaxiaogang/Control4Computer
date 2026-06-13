from flask import Flask, request, render_template_string, abort
import pyautogui
import secrets

app = Flask(__name__)
TOKEN = secrets.token_urlsafe(8)
ALLOWED_KEYS = {"space", "enter", "esc", "up", "down", "left", "right"}
ALLOWED_BUTTONS = {"left", "right"}

PAGE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
  <title>Remote Keys</title>
  <style>
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #101418;
      color: #f5f7fa;
      display: flex;
      align-items: center;
      justify-content: center;
      touch-action: manipulation;
    }
    main {
      width: min(92vw, 460px);
      display: grid;
      gap: 14px;
      padding: 16px 0;
    }
    h1 {
      margin: 0 0 8px;
      text-align: center;
      font-size: 24px;
      font-weight: 700;
    }
    .pad {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      grid-template-rows: repeat(3, 82px);
      gap: 12px;
    }
    .extra, .mouse-buttons {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
    }
    button {
      border: 0;
      border-radius: 18px;
      background: #26313d;
      color: #fff;
      font-size: 30px;
      font-weight: 800;
      box-shadow: 0 8px 18px rgba(0,0,0,.22);
      user-select: none;
      touch-action: none;
    }
    button:active, button.pressed { background: #3d8bfd; transform: translateY(1px); }
    .up { grid-column: 2; grid-row: 1; }
    .left { grid-column: 1; grid-row: 2; }
    .space { grid-column: 2; grid-row: 2; font-size: 22px; }
    .right { grid-column: 3; grid-row: 2; }
    .down { grid-column: 2; grid-row: 3; }
    .extra button, .mouse-buttons button { height: 64px; font-size: 22px; }
    .touchpad {
      height: 190px;
      border-radius: 22px;
      background: #1b232d;
      border: 1px solid #344253;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #7f8c99;
      font-size: 15px;
      user-select: none;
      touch-action: none;
    }
    .touchpad.active { border-color: #3d8bfd; color: #cfe1ff; }
    .hint {
      color: #aab4c0;
      text-align: center;
      font-size: 13px;
      line-height: 1.5;
    }
  </style>
</head>
<body>
  <main>
    <h1>电脑按键遥控</h1>
    <section class="pad">
      <button class="up" data-key="up">↑</button>
      <button class="left" data-key="left">←</button>
      <button class="space" data-key="space">SPACE</button>
      <button class="right" data-key="right">→</button>
      <button class="down" data-key="down">↓</button>
    </section>
    <section class="extra">
      <button data-key="enter">ENTER</button>
      <button data-key="esc">ESC</button>
    </section>
    <div class="touchpad" id="touchpad">触摸板区域</div>
    <section class="mouse-buttons">
      <button data-click="left">左键</button>
      <button data-click="right">右键</button>
    </section>
    <div class="hint">点按触发一次；长按方向键和空格会连续触发。<br>在触摸板区域滑动可移动鼠标。</div>
  </main>

  <script>
    const token = {{ token|tojson }};
    const timers = new Map();
    const touchpad = document.getElementById('touchpad');
    let lastPoint = null;

    async function post(path, body) {
      await fetch(`${path}?token=${encodeURIComponent(token)}`, {
        method: 'POST',
        headers: body ? { 'Content-Type': 'application/json' } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      });
    }

    function press(key) {
      return post(`/press/${key}`);
    }

    function clickMouse(button) {
      return post(`/click/${button}`);
    }

    function moveMouse(dx, dy) {
      return post('/move', { dx, dy });
    }

    function start(button) {
      const key = button.dataset.key;
      if (timers.has(button)) return;
      button.classList.add('pressed');
      press(key);
      if (key === 'enter' || key === 'esc') return;
      timers.set(button, setInterval(() => press(key), key === 'space' ? 220 : 90));
    }

    function stop(button) {
      const timer = timers.get(button);
      if (timer) clearInterval(timer);
      timers.delete(button);
      button.classList.remove('pressed');
    }

    document.querySelectorAll('button[data-key]').forEach(button => {
      button.addEventListener('pointerdown', event => {
        event.preventDefault();
        button.setPointerCapture(event.pointerId);
        start(button);
      });
      button.addEventListener('pointerup', () => stop(button));
      button.addEventListener('pointercancel', () => stop(button));
      button.addEventListener('pointerleave', () => stop(button));
    });

    document.querySelectorAll('button[data-click]').forEach(button => {
      button.addEventListener('click', () => clickMouse(button.dataset.click));
    });

    touchpad.addEventListener('pointerdown', event => {
      event.preventDefault();
      touchpad.setPointerCapture(event.pointerId);
      touchpad.classList.add('active');
      lastPoint = { x: event.clientX, y: event.clientY };
    });

    touchpad.addEventListener('pointermove', event => {
      if (!lastPoint) return;
      event.preventDefault();
      const dx = Math.round((event.clientX - lastPoint.x) * 1.7);
      const dy = Math.round((event.clientY - lastPoint.y) * 1.7);
      lastPoint = { x: event.clientX, y: event.clientY };
      if (dx || dy) moveMouse(dx, dy);
    });

    function stopTouchpad() {
      lastPoint = null;
      touchpad.classList.remove('active');
    }

    touchpad.addEventListener('pointerup', stopTouchpad);
    touchpad.addEventListener('pointercancel', stopTouchpad);
    touchpad.addEventListener('pointerleave', stopTouchpad);
  </script>
</body>
</html>
"""


@app.get("/")
def index():
    if request.args.get("token") != TOKEN:
        return f"打开控制页面：<br><a href='/?token={TOKEN}'>/?token={TOKEN}</a>"
    return render_template_string(PAGE, token=TOKEN)


@app.post("/press/<key>")
def press(key):
    if request.args.get("token") != TOKEN or key not in ALLOWED_KEYS:
        abort(403)
    pyautogui.press(key)
    return {"ok": True}


@app.post("/move")
def move():
    if request.args.get("token") != TOKEN:
        abort(403)
    data = request.get_json() or {}
    dx = max(-80, min(80, int(data.get("dx", 0))))
    dy = max(-80, min(80, int(data.get("dy", 0))))
    pyautogui.moveRel(dx, dy, duration=0)
    return {"ok": True}


@app.post("/click/<button>")
def click(button):
    if request.args.get("token") != TOKEN or button not in ALLOWED_BUTTONS:
        abort(403)
    pyautogui.click(button=button)
    return {"ok": True}


if __name__ == "__main__":
    pyautogui.PAUSE = 0
    print("Remote Keys is running.")
    print(f"Open on this computer: http://127.0.0.1:8000/?token={TOKEN}")
    print("Open on your phone: http://<computer-lan-ip>:8000/ then tap the token link")
    app.run(host="0.0.0.0", port=8000)
