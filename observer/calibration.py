import logging
import socketserver
import threading
from http import server
import cv2
import time
import socket
import keyboard

PAGE = """\
<html>
    <body>
        <div>
            <div style="position: relative; width: 640px; height: 480px">
                <img style="float: left; position: relative; left: 0px; top: 0px;" src="stream.mjpg" width="640" height="480"></img>
                <p style="font-family:consolas; font-size: 10pt; padding: 5px;">switch between high and low quality using 'backspace' (depending on network capacity)
                \nuse 'enter' + numpad arrow keys to calibrate</p>
            </div>
        </div>
    </body>
</html>
"""

stream_img = None


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header(
                'Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                global stream_img
                high_quality = False
                fps, qual = 10, 50
                while True:

                    if keyboard.is_pressed('backspace'):
                        high_quality = not high_quality
                        if high_quality:
                            fps, qual = 60, 95
                            print('switching to high quality streaming')
                        else:
                            fps, qual = 10, 50
                            print('switching to low quality streaming')
                        time.sleep(1.0)

                    img = stream_img[0]
                    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), qual]
                    encimg = cv2.imencode('.jpg', img, encode_param)[1]
                    frame = encimg

                    time.sleep(float(1.0 / fps))

                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

    def log_message(self, format, *args):
        return


class Stream:

    thread_stream = None
    server = None

    def __init__(self, img):
        global stream_img
        stream_img = img
        pass

    def stream(self):
        address = ('', 1337)
        self.server = StreamingServer(address, StreamingHandler)
        self.server.serve_forever()

    def run_stream(self):
        print("initiating stream for calibration")
        self.thread_stream = threading.Thread(
            target=self.stream, name=self.stream, args=(), daemon=True)
        self.thread_stream.start()
        print("stream established at " + get_ip() + ":1337")


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return str(ip)
