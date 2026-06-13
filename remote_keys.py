from flask import Flask, request, render_template_string, abort, redirect
from datetime import datetime
import pyautogui
import secrets
import subprocess

app = Flask(__name__)
TOKEN = secrets.token_urlsafe(8)
ALLOWED_KEYS = {"space", "enter", "esc", "up", "down", "left", "right", "volumedown", "volumeup", "backspace"}
ALLOWED_BUTTONS = {"left", "right"}


def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("remote_keys.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")


PAGE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
  <title>Remote Keys</title>
  <style>
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    html, body {
      height: 100%;
    }
    body {
      margin: 0;
      min-height: 100vh;
      min-height: 100svh;
      min-height: 100dvh;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #101418;
      color: #f5f7fa;
      touch-action: manipulation;
      overflow: hidden;
    }
    main {
      --edge-gap: 12px;
      height: 100vh;
      height: 100svh;
      height: 100dvh;
      position: relative;
      padding: var(--edge-gap);
    }
    .text-send {
      position: absolute;
      left: 50%;
      top: 18px;
      width: min(calc(100vw - 44px), 720px);
      transform: translateX(-50%);
      display: grid;
      grid-template-columns: 2fr 1fr 1fr;
      gap: 10px;
      z-index: 2;
    }
    .text-send input {
      min-width: 0;
      border: 1px solid rgba(255,255,255,.1);
      border-radius: 18px;
      background: rgba(16,20,24,.92);
      color: #fff;
      font-size: 20px;
      padding: 0 16px;
      outline: none;
      box-shadow: 0 10px 26px rgba(0,0,0,.28);
    }
    .text-send input:focus { border-color: #3d8bfd; }
    .text-send button {
      min-width: 0;
      height: 58px;
      font-size: 20px;
    }
    .text-history {
      grid-column: 1 / -1;
      display: none;
      max-height: 220px;
      overflow-y: auto;
      border: 1px solid rgba(255,255,255,.1);
      border-radius: 18px;
      background: rgba(16,20,24,.94);
      box-shadow: 0 10px 26px rgba(0,0,0,.28);
    }
    .text-history.visible:not(:empty) { display: block; }
    .text-history button {
      width: 100%;
      height: 42px;
      border: 0;
      border-radius: 0;
      background: transparent;
      box-shadow: none;
      text-align: left;
      font-size: 16px;
      font-weight: 500;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      backdrop-filter: none;
    }
    .controls {
      --control-edge-gap: 22px;
      --pad-size: calc(100vw - var(--control-edge-gap) * 2);
      --pad-gap: clamp(8px, calc(var(--pad-size) * .03), 14px);
      position: absolute;
      left: 50%;
      bottom: calc(28px + env(safe-area-inset-bottom, 0px));
      width: var(--pad-size);
      transform: translateX(-50%);
      display: grid;
      gap: 10px;
      pointer-events: none;
      z-index: 2;
    }
    .pad {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      grid-template-rows: repeat(3, calc((var(--pad-size) - var(--pad-gap) * 2) / 6));
      gap: var(--pad-gap);
    }
    button {
      border: 1px solid rgba(255,255,255,.08);
      border-radius: clamp(14px, calc(var(--pad-size) * .04), 24px);
      background: rgba(38,49,61,.92);
      color: #fff;
      font-size: clamp(28px, calc(var(--pad-size) * .12), 44px);
      font-weight: 900;
      box-shadow: 0 8px 20px rgba(0,0,0,.34);
      user-select: none;
      touch-action: none;
      pointer-events: auto;
      backdrop-filter: blur(8px);
    }
    button:active, button.pressed { background: #3d8bfd; transform: translateY(1px); }
    .esc { grid-column: 1; grid-row: 1; font-size: clamp(18px, calc(var(--pad-size) * .07), 28px); }
    .up { grid-column: 2; grid-row: 1; }
    .space { grid-column: 3; grid-row: 1; font-size: clamp(16px, calc(var(--pad-size) * .055), 24px); }
    .left { grid-column: 1; grid-row: 2; }
    .enter { grid-column: 2; grid-row: 2; font-size: clamp(16px, calc(var(--pad-size) * .055), 24px); }
    .right { grid-column: 3; grid-row: 2; }
    .volume-down { grid-column: 1; grid-row: 3; font-size: clamp(16px, calc(var(--pad-size) * .055), 24px); }
    .down { grid-column: 2; grid-row: 3; }
    .volume-up { grid-column: 3; grid-row: 3; font-size: clamp(16px, calc(var(--pad-size) * .055), 24px); }
    .touchpad {
      width: 100%;
      height: 100%;
      border-radius: 0;
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
    .fullscreen-toggle {
      position: absolute;
      right: 18px;
      bottom: calc(18px + env(safe-area-inset-bottom, 0px));
      width: 46px;
      height: 46px;
      border-radius: 14px;
      background: rgba(16,20,24,.48);
      font-size: 24px;
      z-index: 3;
      opacity: .72;
    }
    .reconnect-toggle {
      position: absolute;
      left: 18px;
      bottom: calc(18px + env(safe-area-inset-bottom, 0px));
      width: 46px;
      height: 46px;
      border-radius: 14px;
      background: rgba(16,20,24,.48);
      font-size: 20px;
      z-index: 3;
      opacity: .72;
    }
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
    <section class="text-send">
      <input id="textInput" type="search" placeholder="输入要发送到电脑的内容" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false" inputmode="text">
      <button id="sendText" type="button">发送</button>
      <button id="backspace" type="button" data-key="backspace">回退</button>
      <div class="text-history" id="textHistory"></div>
    </section>
    <div class="controls">
      <section class="pad">
        <button class="esc" data-key="esc">ESC</button>
        <button class="up" data-key="up">↑</button>
        <button class="space" data-key="space">SPACE</button>
        <button class="left" data-key="left">←</button>
        <button class="enter" data-key="enter">ENTER</button>
        <button class="right" data-key="right">→</button>
        <button class="volume-down" data-key="volumedown">VOL -</button>
        <button class="down" data-key="down">↓</button>
        <button class="volume-up" data-key="volumeup">VOL +</button>
      </section>
      <div class="hint">单指：移动/点击；双指：滚动。</div>
    </div>
    <button class="reconnect-toggle" id="reconnectToggle" type="button" aria-label="重连">↻</button>
    <button class="fullscreen-toggle" id="fullscreenToggle" type="button" aria-label="切换全屏">⛶</button>
  </main>

  <script>
    let token = {{ token|tojson }};
    const timers = new Map();
    const touchpad = document.getElementById('touchpad');
    const controls = document.querySelector('.controls');
    const textInput = document.getElementById('textInput');
    const textHistory = document.getElementById('textHistory');
    const sendText = document.getElementById('sendText');
    const reconnectToggle = document.getElementById('reconnectToggle');
    const fullscreenToggle = document.getElementById('fullscreenToggle');
    let lastPoint = null;
    let tapPoints = [];
    let activePointers = new Map();
    let scrollPoint = null;
    let longPressTimer = null;

    function updateControlSize() {
      const viewportWidth = window.visualViewport?.width || window.innerWidth;
      const screenWidth = Math.min(screen.width || viewportWidth, screen.availWidth || viewportWidth);
      const width = Math.min(viewportWidth, screenWidth);
      const controlEdgeGap = 22;
      controls.style.setProperty('--pad-size', `${Math.round(Math.max(width - controlEdgeGap * 2, 240))}px`);
    }

    updateControlSize();
    window.addEventListener('resize', updateControlSize);
    window.visualViewport?.addEventListener('resize', updateControlSize);

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

    function scrollMouse(dx, dy) {
      return post('/scroll', { dx, dy });
    }

    function getTextHistory() {
      return JSON.parse(localStorage.getItem('textHistory') || '[]');
    }

    function showTextHistory() {
      textHistory.classList.add('visible');
    }

    function hideTextHistory() {
      textHistory.classList.remove('visible');
    }

    function renderTextHistory() {
      textHistory.replaceChildren(...getTextHistory().map(text => {
        const item = document.createElement('button');
        item.type = 'button';
        item.textContent = text;
        item.addEventListener('pointerdown', event => event.preventDefault());
        item.addEventListener('click', () => {
          textInput.value = text;
          textInput.focus();
          showTextHistory();
        });
        return item;
      }));
    }

    function saveTextHistory(text) {
      const history = getTextHistory().filter(item => item !== text);
      history.unshift(text);
      localStorage.setItem('textHistory', JSON.stringify(history.slice(0, 10)));
      renderTextHistory();
    }

    async function pasteText() {
      const text = textInput.value;
      if (!text) return;
      await post('/paste', { text });
      saveTextHistory(text);
      textInput.value = '';
    }

    function deactivateTextInput() {
      textInput.blur();
      hideTextHistory();
    }

    renderTextHistory();
    textInput.addEventListener('focus', showTextHistory);
    sendText.addEventListener('pointerdown', deactivateTextInput);
    sendText.addEventListener('click', pasteText);
    textInput.addEventListener('keydown', event => {
      if (event.key === 'Enter') {
        event.preventDefault();
        deactivateTextInput();
        pasteText();
      }
    });

    async function toggleFullscreen() {
      deactivateTextInput();
      if (document.fullscreenElement) {
        await document.exitFullscreen();
      } else {
        await document.documentElement.requestFullscreen();
      }
    }

    function updateFullscreenButton() {
      fullscreenToggle.textContent = document.fullscreenElement ? '×' : '⛶';
    }

    reconnectToggle.addEventListener('click', async () => {
      deactivateTextInput();
      timers.forEach(timer => clearInterval(timer));
      timers.clear();
      document.querySelectorAll('button.pressed').forEach(button => button.classList.remove('pressed'));
      activePointers.clear();
      lastPoint = null;
      tapPoints = [];
      scrollPoint = null;
      clearLongPressTimer();
      touchpad.classList.remove('active');
      try {
        const oldToken = token;
        const reconnectResponse = await fetch(`/reconnect?token=${encodeURIComponent(token)}`, {
          method: 'POST',
          cache: 'no-store',
        });
        const reconnectResult = await reconnectResponse.json();
        if (reconnectResult.token) {
          token = reconnectResult.token;
          history.replaceState(null, '', `/?token=${encodeURIComponent(token)}`);
        }
        const healthResponse = await fetch(`/health?token=${encodeURIComponent(token)}`, { cache: 'no-store' });
        console.log('reconnect', {
          oldToken,
          newToken: token,
          matched: reconnectResult.matched,
          reconnectStatus: reconnectResponse.status,
          healthStatus: healthResponse.status,
        });
      } catch (error) {
        console.error('reconnect failed', error);
      }
    });
    fullscreenToggle.addEventListener('click', toggleFullscreen);
    document.addEventListener('fullscreenchange', updateFullscreenButton);

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
        deactivateTextInput();
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

    function averagePoint() {
      const points = [...activePointers.values()];
      return {
        x: points.reduce((sum, point) => sum + point.x, 0) / points.length,
        y: points.reduce((sum, point) => sum + point.y, 0) / points.length,
      };
    }

    touchpad.addEventListener('pointerdown', event => {
      event.preventDefault();
      deactivateTextInput();
      touchpad.setPointerCapture(event.pointerId);
      touchpad.classList.add('active');
      activePointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (activePointers.size >= 2) {
        clearLongPressTimer();
        lastPoint = null;
        tapPoints = [];
        scrollPoint = averagePoint();
        return;
      }
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
        if (!lastPoint || lastPoint.moved || activePointers.size !== 1) return;
        lastPoint.longPressed = true;
        tapPoints = [];
        clickMouse('right');
      }, 650);
    });

    touchpad.addEventListener('pointermove', event => {
      if (!activePointers.has(event.pointerId)) return;
      event.preventDefault();
      activePointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
      if (activePointers.size >= 2) {
        clearLongPressTimer();
        const point = averagePoint();
        if (scrollPoint) {
          const dx = Math.round((point.x - scrollPoint.x) * 5);
          const dy = Math.round((point.y - scrollPoint.y) * 5);
          if (Math.abs(dx) >= 4 || Math.abs(dy) >= 4) scrollMouse(dx, dy);
        }
        scrollPoint = point;
        return;
      }
      if (!lastPoint) return;
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
      activePointers.delete(event.pointerId);
      if (activePointers.size >= 2) {
        scrollPoint = averagePoint();
        return;
      }
      if (event?.type === 'pointerup' && lastPoint && !lastPoint.moved && !lastPoint.longPressed) handleTouchpadTap();
      lastPoint = null;
      scrollPoint = null;
      if (activePointers.size === 0) touchpad.classList.remove('active');
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


@app.post("/reconnect")
def reconnect():
    old_token = request.args.get("token", "")
    log_event(f"reconnect old_token={old_token} current_token={TOKEN} remote={request.remote_addr}")
    return {"ok": True, "token": TOKEN, "matched": old_token == TOKEN}


@app.get("/health")
def health():
    token = request.args.get("token", "")
    ok = token == TOKEN
    log_event(f"health token={token} current_token={TOKEN} ok={ok} remote={request.remote_addr}")
    if not ok:
        abort(403)
    return {"ok": True}


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


@app.post("/scroll")
def scroll():
    if request.args.get("token") != TOKEN:
        abort(403)
    data = request.get_json() or {}
    dx = max(-120, min(120, int(data.get("dx", 0))))
    dy = max(-120, min(120, int(data.get("dy", 0))))
    if dy:
        pyautogui.scroll(-dy)
    if dx:
        pyautogui.hscroll(dx)
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


@app.post("/paste")
def paste():
    if request.args.get("token") != TOKEN:
        abort(403)
    data = request.get_json() or {}
    text = str(data.get("text", ""))[:5000]
    if not text:
        return {"ok": True}
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", "Set-Clipboard -Value ([Console]::In.ReadToEnd())"],
        input=text,
        text=True,
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    pyautogui.hotkey("ctrl", "v")
    return {"ok": True}


if __name__ == "__main__":
    pyautogui.PAUSE = 0
    print("Remote Keys is running.")
    print(f"Open on this computer: http://127.0.0.1:8000/?token={TOKEN}")
    print("Open on your phone: http://<computer-lan-ip>:8000/")
    app.run(host="0.0.0.0", port=8000)
