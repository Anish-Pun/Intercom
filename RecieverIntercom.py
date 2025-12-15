import socket
import subprocess
import threading
import queue
import time
from aiy.leds import Leds, Color
from aiy.board import Board
from aiy.voice import tts

# Configuratie
PORT = 50007
CHUNK = 4096
QUEUE_MAX = 50
LED_HOLD = 0.2

# Queue en socket
q = queue.Queue(maxsize=QUEUE_MAX)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))

# Audio subprocess
play = subprocess.Popen(
    ["aplay", "-q", "-f", "S16_LE", "-c", "1", "-r", "16000"],
    stdin=subprocess.PIPE,
    bufsize=0
)

last_audio_time = 0
mute = False

# Threads
def receiver():
    while True:
        data, _ = sock.recvfrom(CHUNK * 2)
        if not q.full():
            q.put(data)

def player():
    global last_audio_time
    while True:
        data = q.get()
        if not mute:
            try:
                play.stdin.write(data)
                play.stdin.flush()
            except Exception as e:
                print("Audio error:", e)
        last_audio_time = time.time()

def led_manager(leds):
    global last_audio_time, mute
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
        if mute:
            tts.say("Muted", lang='en-GB')
        else:
            tts.say("Unmuted", lang='en-GB')
        time.sleep(0.3)
        
# Start programma
with Board() as board:
    leds = Leds()
    tts.say("Intercom started", lang='en-GB')

    # Start threads
    threading.Thread(target=receiver, daemon=True).start()
    threading.Thread(target=player, daemon=True).start()
    threading.Thread(target=led_manager, args=(leds,), daemon=True).start()
    threading.Thread(target=button_handler, args=(board,), daemon=True).start()

    print("Live receiver running. Button = mute/unmute.")

    while True:
        time.sleep(1)
