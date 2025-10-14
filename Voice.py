import socket
import threading
import pyaudio
from aiy.board import Board, Led

# === CONFIG ===
REMOTE_IP = "192.168.3.153"  # Kit 1
PORT = 50007
CHUNK = 2048
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# === AUDIO SETUP ===
p = pyaudio.PyAudio()
stream_out = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True,
                    frames_per_buffer=CHUNK)

# === SOCKET SETUP ===
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))

# === LISTENER THREAD ===
def listen():
    while True:
        try:
            data, _ = sock.recvfrom(CHUNK*2)
            if data:
                try:
                    stream_out.write(data)
                except IOError:
                    pass
        except Exception as e:
            print("Listener error:", e)

# === TALK FUNCTION ===
def talk():
    with Board() as board:
        print("Push-to-talk intercom running on 192.168.3.80. Hold button to talk.")
        while True:
            board.button.wait_for_press()
            board.led.state = Led.ON

            stream_in = p.open(format=FORMAT,
                               channels=CHANNELS,
                               rate=RATE,
                               input=True,
                               frames_per_buffer=CHUNK)

            stop_event = threading.Event()

            def send_audio():
                while not stop_event.is_set():
                    try:
                        data = stream_in.read(CHUNK, exception_on_overflow=False)
                        sock.sendto(data, (REMOTE_IP, PORT))
                    except IOError:
                        pass

            t = threading.Thread(target=send_audio)
            t.start()

            board.button.wait_for_release()
            stop_event.set()
            t.join()

            stream_in.stop_stream()
            stream_in.close()
            board.led.state = Led.OFF

# === MAIN ===
threading.Thread(target=listen, daemon=True).start()
talk()
