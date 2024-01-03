import io
import logging
import socketserver
from http import server
from threading import Condition, Thread
from spyglass.url_parsing import check_urls_match
from spyglass.exif import create_exif_header
import libcamera
from picamera2.encoders import MJPEGEncoder
from picamera2.outputs import FileOutput
from . import logger
import time
import datetime
import pytz
from suntime import Sun, SunTimeException
latitude = 52.09
longitude = 5.12

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def run_server(bind_address, port, output, picam, stream_url='/stream', snapshot_url='/snapshot', orientation_exif=0):
    exif_header = create_exif_header(orientation_exif)
    class CameraControl(Thread):
        def __init__(self,picam):
            Thread.__init__(self)
            self.picam = picam
            self.sun = Sun(latitude, longitude)
        
        def run(self):
            last_state = "day"
            controls = {}
            while True:
                print(self.picam.start)
                print(self.picam.started)
                print(self.picam.is_open)
                print(self.picam.stop)
                if not self.picam.running:
                    break
                today_sr = self.sun.get_sunrise_time()
                today_ss = self.sun.get_sunset_time()
                now = datetime.datetime.now(pytz.utc)
                print(today_sr)
                print(now)
                print(today_ss)
                if now < today_sr and now > today_ss:
                    print("Night")
                    state = "night"
                    controls = {"ExposureValue": 8, "AnalogueGain": 20}
                else:
                    print("Day")
                    state = "day"
                    controls = {"ExposureValue": 0, "AnalogueGain": 1}
                if state != last_state:
                    last_state = state
                    self.picam.set_controls(controls)
                time.sleep(60*2)
            


    class StreamingHandler(server.BaseHTTPRequestHandler):
        def do_GET(self):
            if check_urls_match(stream_url, self.path):
                self.start_streaming()
            elif check_urls_match(snapshot_url, self.path):
                self.send_snapshot()
            else:
                self.send_error(404)
                self.end_headers()

        def start_streaming(self):
            try:
                self.send_response(200)
                self.send_default_headers()
                self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
                self.end_headers()
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    if exif_header is None:
                        self.send_jpeg_content_headers(frame)
                        self.end_headers()
                        self.wfile.write(frame)
                        self.wfile.write(b'\r\n')
                    else:
                        self.send_jpeg_content_headers(frame, len(exif_header) - 2)
                        self.end_headers()
                        self.wfile.write(exif_header)
                        self.wfile.write(frame[2:])
                        self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning('Removed streaming client %s: %s', self.client_address, str(e))

        def send_snapshot(self):
            try:
                self.send_response(200)
                self.send_default_headers()
                with output.condition:
                    output.condition.wait()
                    frame = output.frame
                if orientation_exif <= 0:
                    self.send_jpeg_content_headers(frame)
                    self.end_headers()
                    self.wfile.write(frame)
                else:
                    self.send_jpeg_content_headers(frame, len(exif_header) - 2)
                    self.end_headers()
                    self.wfile.write(exif_header)
                    self.wfile.write(frame[2:])
            except Exception as e:
                logging.warning(
                    'Removed client %s: %s',
                    self.client_address, str(e))

        def send_default_headers(self):
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')

        def send_jpeg_content_headers(self, frame, extra_len=0):
            self.send_header('Content-Type', 'image/jpeg')
            self.send_header('Content-Length', str(len(frame) + extra_len))

    logger.info('Server listening on %s:%d', bind_address, port)
    logger.info('Streaming endpoint: %s', stream_url)
    logger.info('Snapshot endpoint: %s', snapshot_url)
    address = (bind_address, port)
    camera_control = CameraControl(picam)
    camera_control.start()
    current_server = StreamingServer(address, StreamingHandler)
    current_server.serve_forever()
    camera_control.join()
