import time
import keyboard

from socket import socket, gethostbyname, AF_INET, SOCK_DGRAM
import queue
import sys
import threading

import hardware


class Synchro:

    def __init__(self):
        pass

    t_open = 0
    t_on = time.time()
    obs_on = False

    active = False

    charged_backup = False
    charged = False

    def sync_observer(self, cfg):

        if cfg.remote_keyboard:
            key_pressed = self.sync_remote_key()
        else:
            key_pressed = hardware.gpio.sync_key()

        if cfg.tap == False:
            if key_pressed:
                if self.obs_on == False:
                    self.t_on = time.time()
                    self.obs_on = True
                    self.charged_backup = False
                elif self.active == False and time.time() - self.t_on > cfg.activation_delay / 1000.0:
                    self.active = True
            else:
                self.obs_on = False
                self.active = False
            hardware.gpio.led_green(self.active)
            return

        if key_pressed:
            if self.obs_on == False:
                self.t_on = time.time()
                self.obs_on = True
                self.active = True
                self.charged_backup = False
            elif self.active == False:
                self.active = True
            if self.charged:
                self.charged = False
                self.charged_backup = True
        else:
            if self.charged == False and time.time() - self.t_on < 0.30:
                if self.charged_backup == False:
                    self.charged = True
            self.obs_on = False
            if self.charged == False:
                self.active = False
            elif self.active == False:
                self.charged = False

        if self.active and self.charged == False:
            hardware.gpio.led_green(True)
        elif self.active:
            if time.time() * 1000.0 % cfg.tap_led_time_on + cfg.tap_led_time_off < cfg.tap_led_time_on:
                hardware.gpio.led_green(True)
            else:
                hardware.gpio.led_green(False)
        else:
            hardware.gpio.led_green(False)

    q = queue.Queue()

    def sync_remote_key(self):
        key_pressed = False
        if not self.q.empty():
            key_pressed = self.q.queue[-1]
            if not key_pressed:
                self.q.queue.clear()
        return key_pressed

    def start_remote_keyboard(self):
        thread_remote_keyboard = threading.Thread(
            target=listen_for_remote_keyboard, name=listen_for_remote_keyboard, args=(self.q,), daemon=True)
        thread_remote_keyboard.start()

# remote keyboard functions
# receives key input from the main computer
# requires client to send packages and is hence exposing the system to the anti-cheat


def listen_for_remote_keyboard(q):

    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind((gethostbyname('0.0.0.0'), 5000))
    sock.settimeout(5)
    print("connecting to remote keyboard...")

    t_pressed = time.time()
    while True:
        try:
            data = sock.recvfrom(16)[0]
        except socket.timeout:
            print('no remote keyboard client detected')
            break
        if keyboard.is_pressed('+'):
            break
        b = False
        if str(data)[2] != '0':
            b = True
        if b:
            t_pressed = time.time()
        if time.time() - t_pressed < 0.1:
            q.put(True)
        else:
            q.put(False)
    sys.exit(0)
