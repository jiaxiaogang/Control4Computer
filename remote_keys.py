from flask import Flask, request, render_template_string, abort
import pyautogui
import secrets

app = Flask(__name__)
TOKEN = secrets.token_urlsafe(8)
ALLOWED_KEYS = {"space", "up", "down", "left", "right"}

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
      width: min(92vw, 420px);
      display: grid;
      gap: 14px;
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
      grid-template-rows: repeat(3, 92px);
      gap: 12px;
    }
    button {
      border: 0;
      border-radius: 18px;
      background: #26313d;
      color: #fff;
      font-size: 34px;
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
    <div class="hint">点按触发一次；长按会连续触发。<br>只建议在可信局域网内使用。</div>
  </main>

  <script>
    const token = {{ token|tojson }};
    const timers = new Map();

    async function press(key) {
      await fetch(`/press/${key}?token=${encodeURIComponent(token)}`, { method: 'POST' });
    }

    function start(button) {
      const key = button.dataset.key;
      if (timers.has(button)) return;
      button.classList.add('pressed');
      press(key);
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


if __name__ == "__main__":
    pyautogui.PAUSE = 0
    print("Remote Keys is running.")
    print(f"Open on this computer: http://127.0.0.1:8000/?token={TOKEN}")
    print("Open on your phone: http://<computer-lan-ip>:8000/ then tap the token link")
    app.run(host="0.0.0.0", port=8000)
