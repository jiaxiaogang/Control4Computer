from flask import Flask, request, render_template_string, abort, redirect
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
      touch-action: manipulation;
      overflow: hidden;
    }
    main {
      height: 100vh;
      position: relative;
      padding: 12px;
    }
    .controls {
      position: absolute;
      left: 50%;
      bottom: 18px;
      width: min(calc(100vw - 24px), 720px);
      transform: translateX(-50%);
      display: grid;
      gap: 10px;
      pointer-events: none;
    }
    .pad {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      grid-template-rows: repeat(3, clamp(72px, 12vh, 96px));
      gap: 12px;
    }
    button {
      border: 1px solid rgba(255,255,255,.08);
      border-radius: 22px;
      background: rgba(38,49,61,.92);
      color: #fff;
      font-size: 38px;
      font-weight: 900;
      box-shadow: 0 10px 26px rgba(0,0,0,.34);
      user-select: none;
      touch-action: none;
      pointer-events: auto;
      backdrop-filter: blur(8px);
    }
    button:active, button.pressed { background: #3d8bfd; transform: translateY(1px); }
    .esc { grid-column: 1; grid-row: 1; font-size: 24px; }
    .up { grid-column: 2; grid-row: 1; }
    .space { grid-column: 3; grid-row: 1; font-size: 22px; }
    .left { grid-column: 1; grid-row: 2; }
    .enter { grid-column: 2; grid-row: 2; font-size: 22px; }
    .right { grid-column: 3; grid-row: 2; }
    .down { grid-column: 2; grid-row: 3; }
    .touchpad {
      width: 100%;
      height: 100%;
      border-radius: 26px;
      background: #1b232d;
      border: 1px solid #344253;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #7f8c99;
      font-size: 22px;
      user-select: none;
      touch-action: none;
    }
    .touchpad.active { border-color: #3d8bfd; color: #cfe1ff; }
    .hint {
      color: #c4ced9;
      text-align: center;
      font-size: 14px;
      line-height: 1.4;
      text-shadow: 0 2px 8px rgba(0,0,0,.65);
      pointer-events: none;
    }
  </style>
</head>
<body>
  <main>
    <div class="touchpad" id="touchpad">触摸板区域</div>
    <div class="controls">
      <section class="pad">
        <button class="esc" data-key="esc">ESC</button>
        <button class="up" data-key="up">↑</button>
        <button class="space" data-key="space">SPACE</button>
        <button class="left" data-key="left">←</button>
        <button class="enter" data-key="enter">ENTER</button>
        <button class="right" data-key="right">→</button>
        <button class="down" data-key="down">↓</button>
      </section>
      <div class="hint">触摸板：滑动移动，轻触单击，双击左键，长按右键。</div>
    </div>
  </main>

  <script>
    const token = {{ token|tojson }};
    const timers = new Map();
    const touchpad = document.getElementById('touchpad');
    let lastPoint = null;
    let tapPoints = [];
    let longPressTimer = null;

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

    function doubleClickMouse() {
      return post('/dclick');
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

    function clearLongPressTimer() {
      if (longPressTimer) clearTimeout(longPressTimer);
      longPressTimer = null;
    }

    touchpad.addEventListener('pointerdown', event => {
      event.preventDefault();
      touchpad.setPointerCapture(event.pointerId);
      touchpad.classList.add('active');
      lastPoint = {
        x: event.clientX,
        y: event.clientY,
        startX: event.clientX,
        startY: event.clientY,
        moved: false,
        longPressed: false,
      };
      clearLongPressTimer();
      longPressTimer = setTimeout(() => {
        if (!lastPoint || lastPoint.moved) return;
        lastPoint.longPressed = true;
        tapPoints = [];
        clickMouse('right');
      }, 650);
    });

    touchpad.addEventListener('pointermove', event => {
      if (!lastPoint) return;
      event.preventDefault();
      const dx = Math.round((event.clientX - lastPoint.x) * 1.7);
      const dy = Math.round((event.clientY - lastPoint.y) * 1.7);
      const moved = lastPoint.moved || Math.hypot(event.clientX - lastPoint.startX, event.clientY - lastPoint.startY) > 8;
      lastPoint = {
        ...lastPoint,
        x: event.clientX,
        y: event.clientY,
        moved,
      };
      if (moved) clearLongPressTimer();
      if (dx || dy) moveMouse(dx, dy);
    });

    function handleTouchpadTap() {
      const now = Date.now();
      tapPoints = tapPoints.filter(timestamp => now - timestamp < 320);
      tapPoints.push(now);
      if (tapPoints.length >= 2) {
        tapPoints = [];
        doubleClickMouse();
      } else {
        setTimeout(() => {
          if (tapPoints.length === 1 && Date.now() - tapPoints[0] >= 300) {
            tapPoints = [];
            clickMouse('left');
          }
        }, 310);
      }
    }

    function stopTouchpad(event) {
      clearLongPressTimer();
      if (event?.type === 'pointerup' && lastPoint && !lastPoint.moved && !lastPoint.longPressed) handleTouchpadTap();
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
        return redirect(f"/?token={TOKEN}")
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


@app.post("/dclick")
def double_click():
    if request.args.get("token") != TOKEN:
        abort(403)
    pyautogui.doubleClick()
    return {"ok": True}


if __name__ == "__main__":
    pyautogui.PAUSE = 0
    print("Remote Keys is running.")
    print(f"Open on this computer: http://127.0.0.1:8000/?token={TOKEN}")
    print("Open on your phone: http://<computer-lan-ip>:8000/ then tap the token link")
    app.run(host="0.0.0.0", port=8000)
