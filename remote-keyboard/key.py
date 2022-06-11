import keyboard
from socket import socket, AF_INET, SOCK_DGRAM
import time

IP = '192.168.178.41'
PORT = 5000
SIZE = 16
socket = socket( AF_INET, SOCK_DGRAM )

while True:
    msg = '0'
    if keyboard.is_pressed('umschalt'):
        msg = '1'
    socket.sendto(msg.encode('utf-8'), (IP, PORT))
    time.sleep(0.005)