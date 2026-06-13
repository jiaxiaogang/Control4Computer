from flask import Flask, request, render_template_string, abort, redirect
from datetime import datetime
from time import perf_counter, time
from PIL import Image, ImageDraw
from werkzeug.serving import make_server
import platform
import pyautogui
import pystray
import secrets
import socket
import subprocess
import threading

app = Flask(__name__)
APP_VERSION = "1.0"
TOKEN = secrets.token_urlsafe(8)
ALLOWED_KEYS = {"space", "enter", "esc", "up", "down", "left", "right", "volumedown", "volumeup", "backspace"}
ALLOWED_BUTTONS = {"left", "right"}


def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("remote_keys.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")


def request_diag_start():
    return perf_counter()


def log_request_diag(name, start, detail=""):
    elapsed_ms = (perf_counter() - start) * 1000
    sent_at = request.headers.get("X-Client-Sent-At", "")
    seq = request.headers.get("X-Client-Seq", "")
    inflight = request.headers.get("X-Client-Inflight", "")
    age = ""
    if sent_at:
        try:
            age = f" client_age_ms={(time() * 1000 - float(sent_at)):.1f}"
        except ValueError:
            age = f" client_age_invalid={sent_at}"
    log_event(
        f"diag {name} seq={seq} inflight_at_send={inflight} elapsed_ms={elapsed_ms:.1f}{age} remote={request.remote_addr} {detail}".strip()
    )


PAGE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
  <title>Control4Computer 1.0</title>
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
      grid-template-columns: 3fr .8fr .8fr;
      gap: 8px;
      z-index: 2;
    }
    .text-send input {
      min-width: 0;
      border: 1px solid rgba(255,255,255,.1);
      border-radius: 18px;
      background: rgba(16,20,24,.92);
      color: #fff;
      font-size: 16px;
      padding: 0 14px;
      outline: none;
      box-shadow: 0 10px 26px rgba(0,0,0,.28);
    }
    .text-send input:focus { border-color: #3d8bfd; }
    .text-send input::placeholder { font-size: 14px; }
    .text-send button {
      min-width: 0;
      height: 40px;
      font-size: 14px;
    }
    .text-history {
      grid-column: 1 / -1;
      display: none;
      max-height: 220px;
      overflow-y: scroll;
      touch-action: pan-y;
      -webkit-overflow-scrolling: touch;
      overscroll-behavior: contain;
      border: 1px solid rgba(255,255,255,.1);
      border-radius: 18px;
      background: rgba(16,20,24,.94);
      box-shadow: 0 10px 26px rgba(0,0,0,.28);
    }
    .text-history.visible:not(:empty) { display: block; }
    .text-history-item {
      width: 100%;
      min-height: 42px;
      padding: 10px 16px;
      color: #fff;
      text-align: left;
      font-size: 16px;
      font-weight: 400;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      user-select: none;
      touch-action: pan-y;
    }
    .text-history-item:active { background: rgba(61,139,253,.3); }
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
      font-size: clamp(24px, calc(var(--pad-size) * .095), 36px);
      font-weight: 500;
      box-shadow: 0 8px 20px rgba(0,0,0,.34);
      user-select: none;
      touch-action: none;
      pointer-events: auto;
      backdrop-filter: blur(8px);
    }
    button:active, button.pressed { background: #3d8bfd; transform: translateY(1px); }
    .esc { grid-column: 1; grid-row: 1; }
    .up { grid-column: 2; grid-row: 1; }
    .space { grid-column: 3; grid-row: 1; }
    .left { grid-column: 1; grid-row: 2; }
    .enter { grid-column: 2; grid-row: 2; }
    .right { grid-column: 3; grid-row: 2; }
    .volume-down { grid-column: 1; grid-row: 3; }
    .down { grid-column: 2; grid-row: 3; }
    .volume-up { grid-column: 3; grid-row: 3; }
    .esc, .space, .enter, .volume-down, .volume-up { font-size: clamp(14px, calc(var(--pad-size) * .045), 20px); }
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
    .floating-actions {
      position: absolute;
      right: 16px;
      bottom: calc(16px + env(safe-area-inset-bottom, 0px));
      display: flex;
      gap: 8px;
      z-index: 3;
    }
    .floating-actions button {
      width: 34px;
      height: 34px;
      border-radius: 10px;
      background: rgba(16,20,24,.48);
      font-size: 18px;
      opacity: .72;
    }
    .reconnect-toggle {
      position: absolute;
      left: 16px;
      bottom: calc(16px + env(safe-area-inset-bottom, 0px));
      width: 34px;
      height: 34px;
      border-radius: 10px;
      background: rgba(16,20,24,.48);
      font-size: 16px;
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
    <div class="floating-actions">
      <button id="vibrationDown" type="button" aria-label="减弱震感">−</button>
      <button id="vibrationUp" type="button" aria-label="增强震感">+</button>
      <button id="fullscreenToggle" type="button" aria-label="切换全屏">⛶</button>
    </div>
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
    const vibrationDown = document.getElementById('vibrationDown');
    const vibrationUp = document.getElementById('vibrationUp');
    const fullscreenToggle = document.getElementById('fullscreenToggle');
    let lastPoint = null;
    let tapPoints = [];
    let activePointers = new Map();
    let scrollPoint = null;
    let twoFingerTap = null;
    let longPressTimer = null;
    let lastMoveVibrateAt = 0;
    let vibrationScale = Number(localStorage.getItem('vibrationScale')) || 1;

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

    let requestSeq = 0;
    let inflightRequests = 0;

    async function post(path, body) {
      const seq = ++requestSeq;
      const sentAt = Date.now();
      const inflightAtSend = inflightRequests;
      inflightRequests += 1;
      try {
        await fetch(`${path}?token=${encodeURIComponent(token)}`, {
          method: 'POST',
          headers: {
            'X-Client-Sent-At': String(sentAt),
            'X-Client-Seq': String(seq),
            'X-Client-Inflight': String(inflightAtSend),
            ...(body ? { 'Content-Type': 'application/json' } : {}),
          },
          body: body ? JSON.stringify(body) : undefined,
        });
      } finally {
        inflightRequests -= 1;
      }
    }

    function press(key) {
      return post(`/press/${key}`);
    }

    function clickMouse(button) {
      vibrate();
      return post(`/click/${button}`);
    }

    function vibrate(duration = 75) {
      if (navigator.vibrate) navigator.vibrate(Math.round(duration * vibrationScale));
    }

    function vibrateDuringMove() {
      const now = Date.now();
      if (now - lastMoveVibrateAt < 90) return;
      lastMoveVibrateAt = now;
      vibrate(50);
    }

    function doubleClickMouse() {
      vibrate();
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
        const item = document.createElement('div');
        item.className = 'text-history-item';
        item.textContent = text;
        item.addEventListener('click', () => {
          vibrate();
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
      vibrate();
      await post('/paste', { text });
      saveTextHistory(text);
      textInput.value = '';
    }

    function deactivateTextInput() {
      textInput.blur();
      hideTextHistory();
    }

    renderTextHistory();
    textHistory.addEventListener('pointerdown', event => event.stopPropagation());
    textHistory.addEventListener('pointermove', event => event.stopPropagation());
    textHistory.addEventListener('pointerup', event => event.stopPropagation());
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
      vibrate();
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
      vibrate();
      deactivateTextInput();
      timers.forEach(timer => clearInterval(timer));
      timers.clear();
      document.querySelectorAll('button.pressed').forEach(button => button.classList.remove('pressed'));
      activePointers.clear();
      lastPoint = null;
      tapPoints = [];
      scrollPoint = null;
      twoFingerTap = null;
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
    vibrationDown.addEventListener('click', () => {
      vibrationScale /= 1.3;
      localStorage.setItem('vibrationScale', String(vibrationScale));
      vibrate();
    });
    vibrationUp.addEventListener('click', () => {
      vibrationScale *= 1.3;
      localStorage.setItem('vibrationScale', String(vibrationScale));
      vibrate();
    });
    fullscreenToggle.addEventListener('click', toggleFullscreen);
    document.addEventListener('fullscreenchange', updateFullscreenButton);

    function start(button) {
      const key = button.dataset.key;
      if (timers.has(button)) return;
      vibrate();
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
        twoFingerTap = { ...scrollPoint, moved: false };
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
        if (twoFingerTap && Math.hypot(point.x - twoFingerTap.x, point.y - twoFingerTap.y) > 10) {
          twoFingerTap.moved = true;
        }
        if (scrollPoint) {
          const dx = Math.round((point.x - scrollPoint.x) * 5);
          const dy = Math.round((point.y - scrollPoint.y) * 5);
          if (Math.abs(dx) >= 4 || Math.abs(dy) >= 4) {
            vibrateDuringMove();
            scrollMouse(dx, dy);
          }
        }
        scrollPoint = point;
        return;
      }
      if (!lastPoint) return;
      const dx = Math.round((event.clientX - lastPoint.x) * 5.1);
      const dy = Math.round((event.clientY - lastPoint.y) * 5.1);
      const moved = lastPoint.moved || Math.hypot(event.clientX - lastPoint.startX, event.clientY - lastPoint.startY) > 8;
      lastPoint = {
        ...lastPoint,
        x: event.clientX,
        y: event.clientY,
        moved,
      };
      if (moved) clearLongPressTimer();
      if (dx || dy) {
        vibrateDuringMove();
        moveMouse(dx, dy);
      }
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
      if (event?.type === 'pointerup' && twoFingerTap && !twoFingerTap.moved && !lastPoint) {
        clickMouse('right');
      } else if (event?.type === 'pointerup' && lastPoint && !lastPoint.moved && !lastPoint.longPressed) {
        handleTouchpadTap();
      }
      lastPoint = null;
      scrollPoint = null;
      twoFingerTap = null;
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
    start = request_diag_start()
    if request.args.get("token") != TOKEN or key not in ALLOWED_KEYS:
        abort(403)
    press_key(key)
    log_request_diag("press", start, f"key={key}")
    return {"ok": True}


@app.post("/move")
def move():
    start = request_diag_start()
    if request.args.get("token") != TOKEN:
        abort(403)
    data = request.get_json() or {}
    dx = max(-80, min(80, int(data.get("dx", 0))))
    dy = max(-80, min(80, int(data.get("dy", 0))))
    pyautogui.moveRel(dx, dy, duration=0)
    log_request_diag("move", start, f"dx={dx} dy={dy}")
    return {"ok": True}


@app.post("/scroll")
def scroll():
    start = request_diag_start()
    if request.args.get("token") != TOKEN:
        abort(403)
    data = request.get_json() or {}
    dx = max(-120, min(120, int(data.get("dx", 0))))
    dy = max(-120, min(120, int(data.get("dy", 0))))
    if dy:
        pyautogui.scroll(-dy)
    if dx:
        pyautogui.hscroll(dx)
    log_request_diag("scroll", start, f"dx={dx} dy={dy}")
    return {"ok": True}


@app.post("/click/<button>")
def click(button):
    start = request_diag_start()
    if request.args.get("token") != TOKEN or button not in ALLOWED_BUTTONS:
        abort(403)
    pyautogui.click(button=button)
    log_request_diag("click", start, f"button={button}")
    return {"ok": True}


@app.post("/dclick")
def double_click():
    start = request_diag_start()
    if request.args.get("token") != TOKEN:
        abort(403)
    pyautogui.doubleClick()
    log_request_diag("dclick", start)
    return {"ok": True}


@app.post("/paste")
def paste():
    start = request_diag_start()
    if request.args.get("token") != TOKEN:
        abort(403)
    data = request.get_json() or {}
    text = str(data.get("text", ""))[:5000]
    if not text:
        log_request_diag("paste", start, "empty=true")
        return {"ok": True}
    copy_to_clipboard(text)
    if platform.system() == "Darwin":
        pyautogui.hotkey("command", "v")
    else:
        pyautogui.hotkey("ctrl", "v")
    log_request_diag("paste", start, f"chars={len(text)}")
    return {"ok": True}


def create_tray_image():
    image = Image.new("RGBA", (64, 64), (16, 20, 24, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 56, 56), radius=12, fill=(61, 139, 253, 255))
    draw.rectangle((22, 18, 42, 40), fill=(255, 255, 255, 255))
    draw.polygon([(18, 40), (46, 40), (40, 50), (24, 50)], fill=(255, 255, 255, 255))
    return image


def get_lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def get_lan_url():
    return f"http://{get_lan_ip()}:8000/"


def press_key(key):
    if platform.system() == "Darwin" and key in {"volumeup", "volumedown"}:
        direction = "+" if key == "volumeup" else "-"
        subprocess.run(
            [
                "osascript",
                "-e",
                f"set volume output volume ((output volume of (get volume settings)) {direction} 5)",
            ],
            check=True,
        )
        return

    pyautogui.press(key)


def copy_to_clipboard(text):
    if platform.system() == "Darwin":
        subprocess.run(["pbcopy"], input=text, text=True, check=True)
        return

    subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", "Set-Clipboard -Value ([Console]::In.ReadToEnd())"],
        input=text,
        text=True,
        check=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def run_server(server):
    print(f"Control4Computer {APP_VERSION} is running.")
    print(f"Open on this computer: http://127.0.0.1:8000/?token={TOKEN}")
    print(f"Open on your phone: {get_lan_url()}")
    server.serve_forever()


def run_tray(server):
    lan_url = get_lan_url()

    def copy_address(icon, item):
        copy_to_clipboard(lan_url)
        log_event(f"tray copy address {lan_url}")

    def exit_app(icon, item):
        log_event("tray exit")
        icon.stop()
        threading.Thread(target=server.shutdown, daemon=True).start()

    icon = pystray.Icon(
        "Control4Computer",
        create_tray_image(),
        f"Control4Computer {APP_VERSION}",
        pystray.Menu(
            pystray.MenuItem(lan_url, None, enabled=False),
            pystray.MenuItem("复制地址", copy_address),
            pystray.MenuItem("退出", exit_app),
        ),
    )
    icon.run()


if __name__ == "__main__":
    pyautogui.PAUSE = 0
    pyautogui.FAILSAFE = False
    server = make_server("0.0.0.0", 8000, app, threaded=True)
    threading.Thread(target=run_server, args=(server,), daemon=True).start()
    run_tray(server)
