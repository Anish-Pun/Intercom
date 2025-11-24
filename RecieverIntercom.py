import socket
import subprocess
import threading
import queue
import time
from aiy.leds import Leds, Color

PORT = 50007
CHUNK = 4096
QUEUE_MAX = 50
LED_HOLD = 0.2

q = queue.Queue(maxsize=QUEUE_MAX)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))

play = subprocess.Popen(
    ["aplay", "-q", "-f", "S16_LE", "-c", "1", "-r", "16000"],
    stdin=subprocess.PIPE
)

leds = Leds()
last_audio_time = 0

def receiver():
    while True:
        data, _ = sock.recvfrom(CHUNK * 2)
        if not q.full():
            q.put(data)

def player():
    global last_audio_time
    while True:
        data = q.get()
        play.stdin.write(data)
        last_audio_time = time.time()

def led_manager():
    while True:
        if time.time() - last_audio_time < LED_HOLD:
            leds.update(Leds.rgb_on(Color.GREEN))
        else:
            leds.update(Leds.rgb_off())
        time.sleep(0.02)

threading.Thread(target=receiver, daemon=True).start()
threading.Thread(target=player, daemon=True).start()
threading.Thread(target=led_manager, daemon=True).start()

print("Live receiver running with green LED indicator...")
while True:
    time.sleep(1)
