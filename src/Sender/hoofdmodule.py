import socket
import subprocess
import threading
import time
import wave
import RPi.GPIO as GPIO

# 4 kamerknoppen + 5e "alle kamers" + 6e sirene
BTN_ROOM1 = 17
BTN_ROOM2 = 6
BTN_ROOM3 = 13
BTN_ROOM4 = 19
BTN_ALL   = 27
BTN_SIREN = 21

ROOMS = {
    1: ("192.168.3.192", 50007),
    2: ("192.168.3.80",  50007),
    3: ("192.168.3.153", 50007),
    4: ("192.168.3.225", 50007),
}

CHUNK = 4096
MIC_CMD = [
    "arecord", "-q",
    "-f", "S16_LE",
    "-c", "1",
    "-r", "16000",
    "-"
]

SIREN_WAV = "/home/pxl-anpr/intercom/sirene.wav"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
for pin in [BTN_ROOM1, BTN_ROOM2, BTN_ROOM3, BTN_ROOM4, BTN_ALL, BTN_SIREN]:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Sirene-status (toggle)
siren_on = False


def get_active_rooms():
    r1 = GPIO.input(BTN_ROOM1) == GPIO.LOW
    r2 = GPIO.input(BTN_ROOM2) == GPIO.LOW
    r3 = GPIO.input(BTN_ROOM3) == GPIO.LOW
    r4 = GPIO.input(BTN_ROOM4) == GPIO.LOW
    all_rooms = GPIO.input(BTN_ALL) == GPIO.LOW

    if all_rooms:
        print("ALL knop ingedrukt -> alle kamers actief")
        return set(ROOMS.keys())

    active = set()
    if r1:
        active.add(1)
        print("Kamer 1 knop ingedrukt")
    if r2:
        active.add(2)
        print("Kamer 2 knop ingedrukt")
    if r3:
        active.add(3)
        print("Kamer 3 knop ingedrukt")
    if r4:
        active.add(4)
        print("Kamer 4 knop ingedrukt")

    return active


def mic_sender():
    arec = subprocess.Popen(MIC_CMD, stdout=subprocess.PIPE, bufsize=0)
    try:
        while True:
            data = arec.stdout.read(CHUNK)
            if not data:
                break
            # optioneel: microfoon uitschakelen tijdens sirene
            if siren_on:
                continue
            targets = get_active_rooms()
            if not targets:
                continue
            for rid in targets:
                addr = ROOMS[rid]
                sock.sendto(data, addr)
    finally:
        arec.terminate()


def siren_sender():
    """Stuurt sirene.wav continu naar alle kamers zolang siren_on True is."""
    global siren_on
    while True:
        if not siren_on:
            time.sleep(0.05)
            continue

        try:
            with wave.open(SIREN_WAV, "rb") as wf:
                nchannels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                if not (nchannels == 1 and sampwidth == 2 and framerate == 16000):
                    print("WAARSCHUWING: sirene.wav is niet mono/16bit/16kHz")

                while siren_on:
                    # 16-bit mono -> 2 bytes per sample
                    data = wf.readframes(CHUNK // 2)
                    if not data:
                        wf.rewind()
                        continue
                    for rid, addr in ROOMS.items():
                        sock.sendto(data, addr)
        except FileNotFoundError:
            print("sirene.wav niet gevonden:", SIREN_WAV)
            time.sleep(1)


def siren_handler():
    """Toggle sirene aan/uit met de sirene-knop."""
    global siren_on
    prev_state = GPIO.input(BTN_SIREN)
    while True:
        state = GPIO.input(BTN_SIREN)
        if prev_state == GPIO.HIGH and state == GPIO.LOW:
            siren_on = not siren_on
            print("Sirene AAN" if siren_on else "Sirene UIT")
        prev_state = state
        time.sleep(0.02)


if __name__ == "__main__":
    try:
        threading.Thread(target=mic_sender,   daemon=True).start()
        threading.Thread(target=siren_sender, daemon=True).start()
        threading.Thread(target=siren_handler, daemon=True).start()
        print("Hoofdmodule gestart, microfoon & sirene worden geroute naar kamers.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        GPIO.cleanup()
