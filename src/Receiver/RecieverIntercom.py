import socket
import threading
import time
import queue
import numpy as np
from flask import Flask, request, render_template, jsonify
from aiy.board import Board
from aiy.leds import Leds, Color
from aiy.voice import tts
import subprocess
import os

# ================== CONFIG ==================
UDP_IP = ""
UDP_PORT = 50007
CHUNK = 2048
RATE = 16000
LED_HOLD = 0.5

PEERS = {
    "kit1": "192.168.3.80",
    "kit2": "192.168.3.153",
    "kit3": "192.168.3.225"
}

# ================== STATE ==================
mute = False
volume = 1.0
last_audio_time = 0
last_user_ip = "None"
current_audio_level = 0.0
tx_target = None
start_time = time.time()

tx_lock = threading.Lock()
leds = None

# ================== AUDIO ==================
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

q = queue.Queue(maxsize=10)

play = subprocess.Popen(
    ["aplay", "-f", "S16_LE", "-r", str(RATE), "-c", "1"],
    stdin=subprocess.PIPE
)

rec = subprocess.Popen(
    ["arecord", "-f", "S16_LE", "-r", str(RATE), "-c", "1"],
    stdout=subprocess.PIPE
)

# ================== WEB UI ==================
app = Flask(__name__)

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/set_volume")
def set_volume():
    global volume
    v = float(request.args.get("vol", 100))
    volume = max(0.0, min(v / 100.0, 1.0))
    return "OK"

@app.route("/toggle_mute")
def toggle_mute():
    global mute
    mute = not mute
    tts.say("Muted" if mute else "Unmuted", lang="en-GB")
    return jsonify({"mute": mute})

@app.route("/set_target", methods=["POST"])
def set_target():
    global tx_target
    data = request.json
    target = data.get("target")

    with tx_lock:
        if not target:
            tx_target = None
        elif target == "broadcast":
            tx_target = "broadcast"
        elif target in PEERS:
            tx_target = PEERS[target]
        else:
            tx_target = None

    return jsonify({"tx_target": tx_target})

@app.route("/status")
def status():
    now = time.time()
    with tx_lock:
        target = tx_target

    return jsonify({
        "mute": mute,
        "audio_level": float(current_audio_level),
        "last_user_ip": last_user_ip,
        "connected": (now - last_audio_time) < 3,
        "tx_target": target,
        "peers": PEERS
    })

@app.route("/info")
def info():
    uptime = int(time.time() - start_time)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "Unknown"

    return jsonify({
        "hostname": os.uname().nodename,
        "ip": ip,
        "udp_port": UDP_PORT,
        "http_port": 8080,
        "uptime": uptime
    })

def start_web():
    app.run(host="0.0.0.0", port=8080)

# ================== THREADS ==================
def receiver():
    global last_user_ip
    while True:
        data, addr = sock.recvfrom(CHUNK * 2)
        last_user_ip = addr[0]
        if not q.full():
            q.put(data)

def player():
    global last_audio_time, current_audio_level
    while True:
        data = q.get()
        last_audio_time = time.time()

        if mute:
            continue

        audio = np.frombuffer(data, dtype=np.int16)
        current_audio_level = float(
            np.sqrt(np.mean(audio.astype(np.float32) ** 2)) / 32768
        )

        audio = np.clip(audio * volume, -32768, 32767).astype(np.int16)

        try:
            play.stdin.write(audio.tobytes())
            play.stdin.flush()
        except:
            pass

def sender():
    while True:
        with tx_lock:
            target = tx_target

        if not target or mute:
            time.sleep(0.05)
            continue

        try:
            data = rec.stdout.read(CHUNK * 2)

            if target == "broadcast":
                for ip in PEERS.values():
                    sock.sendto(data, (ip, UDP_PORT))
            else:
                sock.sendto(data, (target, UDP_PORT))

        except Exception as e:
            print("Sender error:", e)
            time.sleep(0.1)

def led_manager():
    while True:
        if mute:
            leds.update(Leds.rgb_on(Color.RED))
        elif time.time() - last_audio_time < LED_HOLD:
            leds.update(Leds.rgb_on(Color.GREEN))
        else:
            leds.update(Leds.rgb_on(Color.BLUE))
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
        threading.Thread(target=sender, daemon=True).start()
        threading.Thread(target=led_manager, daemon=True).start()
        threading.Thread(target=button_handler, args=(board,), daemon=True).start()
        threading.Thread(target=start_web, daemon=True).start()

        print("Intercom running")
        print("Web UI: http://<PI_IP>:8080")

        while True:
            time.sleep(1)

except KeyboardInterrupt:
    pass

finally:
    try:
        leds.update(Leds.rgb_off())
    except:
        pass
