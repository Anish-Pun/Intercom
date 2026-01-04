import socket
import threading
import time
import queue
import numpy as np
from flask import Flask, request, render_template
from aiy.board import Board
from aiy.leds import Leds, Color
from aiy.voice import tts
import subprocess

# ================== CONFIG ==================
UDP_IP = ""
UDP_PORT = 50007
CHUNK = 2048
CALL_TIMEOUT = 2.0
LED_HOLD = 0.5

# ================== STATE ==================
mute = False
volume = 1.0
call_active = False
last_audio_time = 0
leds = None

# ================== AUDIO ==================
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

q = queue.Queue(maxsize=10)

play = subprocess.Popen(
    ["aplay", "-f", "S16_LE", "-r", "16000", "-c", "1"],
    stdin=subprocess.PIPE
)

# ================== WEB ==================
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("dashboard.html", vol=int(volume * 100))

@app.route("/set_volume")
def set_volume():
    global volume
    v = float(request.args.get("vol", 100))
    volume = max(0.0, min(v / 100.0, 1.0))
    return "OK"

@app.route("/toggle_mute", methods=["POST"])
def toggle_mute():
    global mute
    mute = not mute
    tts.say("Muted" if mute else "Unmuted", lang="en-GB")
    return "OK"

@app.route("/status")
def status():
    return {
        "mute": mute,
        "call_active": call_active
    }

def start_web():
    app.run(host="0.0.0.0", port=8080)

# ================== THREADS ==================
def receiver():
    while True:
        data, _ = sock.recvfrom(CHUNK * 2)
        if not q.full():
            q.put(data)

def player():
    global last_audio_time, call_active
    while True:
        data = q.get()
        now = time.time()

        call_active = True

        if not mute:
            audio = np.frombuffer(data, dtype=np.int16)
            audio = np.clip(audio * volume, -32768, 32767).astype(np.int16)
            try:
                play.stdin.write(audio.tobytes())
                play.stdin.flush()
            except:
                pass

        last_audio_time = now

def call_watcher():
    global call_active
    while True:
        if call_active and time.time() - last_audio_time > CALL_TIMEOUT:
            call_active = False
        time.sleep(0.2)

def led_manager():
    global leds
    while True:
        if mute:
            leds.update(Leds.rgb_on(Color.RED))        # Muted
        elif call_active and time.time() - last_audio_time < LED_HOLD:
            leds.update(Leds.rgb_on(Color.GREEN))      # Audio playing
        elif call_active:
            leds.update(Leds.rgb_on(Color.YELLOW))     # Call active
        else:
            leds.update(Leds.rgb_on(Color.BLUE))       # Idle
        time.sleep(0.1)

def button_handler(board):
    global mute
    while True:
        board.button.wait_for_press()
        mute = not mute
        tts.say("Muted" if mute else "Unmuted", lang="en-GB")
        time.sleep(0.3)

# ================== MAIN ==================
try:
    with Board() as board:
        leds = Leds()
        tts.say("Intercom started", lang="en-GB")

        threading.Thread(target=receiver, daemon=True).start()
        threading.Thread(target=player, daemon=True).start()
        threading.Thread(target=call_watcher, daemon=True).start()
        threading.Thread(target=led_manager, daemon=True).start()
        threading.Thread(target=button_handler, args=(board,), daemon=True).start()
        threading.Thread(target=start_web, daemon=True).start()

        print("Intercom running")
        print("Button = mute/unmute")
        print("Dashboard: http://<PI_IP>:8080")

        while True:
            time.sleep(1)

except KeyboardInterrupt:
    print("Shutting down intercom...")

finally:
    try:
        if leds:
            leds.update(Leds.rgb_off())
    except:
        pass
