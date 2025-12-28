import socket
import subprocess
import threading
import time
import RPi.GPIO as GPIO

# 4 kamerknoppen + 5e "alle kamers" + 6e sirene
BTN_ROOM1 = 5
BTN_ROOM2 = 6
BTN_ROOM3 = 13
BTN_ROOM4 = 19
BTN_ALL   = 26
BTN_SIREN = 21

# IP's en poorten van de AIY-kits
ROOMS = {
    1: ("192.168.1.101", 50001),
    2: ("192.168.1.102", 50002),
    3: ("192.168.1.103", 50003),
    4: ("192.168.1.104", 50004),
}

CHUNK = 4096
MIC_CMD = [
    "arecord", "-q",
    "-f", "S16_LE",
    "-c", "1",
    "-r", "16000",
    "-"
]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

GPIO.setmode(GPIO.BCM)
for pin in [BTN_ROOM1, BTN_ROOM2, BTN_ROOM3, BTN_ROOM4, BTN_ALL, BTN_SIREN]:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def get_active_rooms():
    # Lees knoppen (laag = ingedrukt)
    r1 = GPIO.input(BTN_ROOM1) == GPIO.LOW
    r2 = GPIO.input(BTN_ROOM2) == GPIO.LOW
    r3 = GPIO.input(BTN_ROOM3) == GPIO.LOW
    r4 = GPIO.input(BTN_ROOM4) == GPIO.LOW
    all_rooms = GPIO.input(BTN_ALL) == GPIO.LOW

    active = set()
    if all_rooms:
        active = set(ROOMS.keys())
    else:
        if r1: active.add(1)
        if r2: active.add(2)
        if r3: active.add(3)
        if r4: active.add(4)
    return active

def mic_sender():
    # Start microfoon-capture
    arec = subprocess.Popen(MIC_CMD, stdout=subprocess.PIPE, bufsize=0)
    try:
        while True:
            data = arec.stdout.read(CHUNK)
            if not data:
                break
            targets = get_active_rooms()
            for rid in targets:
                addr = ROOMS[rid]
                sock.sendto(data, addr)
    finally:
        arec.terminate()

def siren_handler():
    # Later uitwerken: bv. WAV afspelen lokaal + UDP naar alle rooms
    while True:
        if GPIO.input(BTN_SIREN) == GPIO.LOW:
            print("Sirene-knop ingedrukt (hier sirene-code toevoegen)")
            time.sleep(0.3)  # debounce
        time.sleep(0.05)

if __name__ == "__main__":
    try:
        threading.Thread(target=mic_sender, daemon=True).start()
        threading.Thread(target=siren_handler, daemon=True).start()
        print("Hoofdmodule gestart, microfoon wordt geroute naar kamers.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()
