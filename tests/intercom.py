import time
import threading
import socket
from aiy.board import Board
from aiy.voice.audio import AudioFormat, record_file
from aiy.leds import Leds, Pattern, Color

TARGET_IP = '192.168.0.181'
PORT = 5001
FILENAME = 'recording.wav'


def send_file(file_path, target_ip, port=5001):
    with socket.socket() as s:
        s.connect((target_ip, port))
        with open(file_path, 'rb') as f:
            s.sendfile(f)
    print(f'Audio sent to {target_ip}:{port}')


def main():
    with Board() as board, Leds() as leds:
        print('Press button to start recording.')
        board.button.wait_for_press()

        done = threading.Event()

        # LED blinks while recording
        def led_blink():
            leds.pattern = Pattern.blink(500)
            leds.update(Leds.rgb_pattern(Color.RED))
            while not done.is_set():
                time.sleep(0.1)
            leds.update(Leds.rgb_off())

        led_thread = threading.Thread(target=led_blink)
        led_thread.start()

        start = time.monotonic()

        def wait():
            while not done.is_set():
                duration = time.monotonic() - start
                print(f'Recording: {duration:.02f} seconds [Press button to stop]')
                time.sleep(0.5)

        # Stop when button is pressed again
        board.button.when_pressed = done.set

        # Start recording (blocks until done is set)
        record_file(AudioFormat.CD, filename=FILENAME, wait=wait, filetype='wav')
        done.set()
        led_thread.join()

        print(f'Sending {FILENAME} to {TARGET_IP}...')
        send_file(FILENAME, TARGET_IP, PORT)


if name == 'main':
    main()
