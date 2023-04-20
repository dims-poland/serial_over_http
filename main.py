# This is a sample Python script.
import argparse
# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


import http.server
import logging
from functools import partial

import serial
import socketserver
import time
import sys

# import safe_termination

DEFAULTS = dict(
    serial_device='COM6',
    http_server_address='127.0.0.1',
    http_server_port=8888,
    baud_rate=9600,
    retry_interval=5,
    num_write_retries=5,
    num_serial_open_retries=100,
    http_content_type='text/plain',
    serial_encoding='utf-8',
    http_encoding='utf-8',
    open_during_init=True,
    server_logger_name='SerialToHttpServer',
    handler_logger_name='SerialToHttpHandler',
)


class SerialToHTTPServer(http.server.HTTPServer):

    def __init__(
            self,
            server_address=(DEFAULTS['http_server_address'], DEFAULTS['http_server_port']),
            bind_and_activate=True,
            serial_device=DEFAULTS['serial_device'],
            baud_rate=DEFAULTS['baud_rate'],
            num_serial_open_retries=DEFAULTS['num_serial_open_retries'],
            retry_interval=DEFAULTS['retry_interval'],
            num_write_retries=DEFAULTS['num_write_retries'],
            server_logger_name=DEFAULTS['server_logger_name'],
            handler_logger_name=DEFAULTS['handler_logger_name'],
            http_content_type=DEFAULTS['http_content_type'],
            serial_encoding=DEFAULTS['serial_encoding'],
            http_encoding=DEFAULTS['http_encoding'],
            open_during_init=True
    ):
        serial_to_http_handler_with_args = partial(
            SerialToHttpHandler,
            retry_interval=retry_interval,
            num_write_retries=num_write_retries,
            logger_name=handler_logger_name,
            http_content_type=http_content_type,
            serial_encoding=serial_encoding,
            http_encoding=http_encoding,
        )
        super().__init__(
            server_address=server_address,
            RequestHandlerClass=serial_to_http_handler_with_args,
            bind_and_activate=bind_and_activate)

        self.logger = logging.getLogger(server_logger_name)
        self.serial_device = serial_device
        self.baud_rate = baud_rate
        self.serial_conn = None
        self.num_serial_open_retries = num_serial_open_retries
        self.retry_interval = retry_interval
        open_during_init = open_during_init
        if open_during_init:
            self.open_serial_conn()

    def open_serial_conn(self, force=False):
        if not self.serial_conn or not self.serial_conn.isOpen() or force:
            if bool(self.serial_conn):
                try:
                    self.serial_conn.close()
                except:
                    pass
            retries = 0
            last_error = None
            while True:
                try:
                    self.serial_conn = serial.Serial(self.serial_device, self.baud_rate)
                    break
                except Exception as e:
                    this_error = str(e)
                    if last_error != this_error:
                        self.logger.error(f"Failed to open serial port: [{e.__class__.__name__}]{e}")
                        last_error = this_error
                    time.sleep(self.retry_interval)
                    retries += 1
                    if self.num_serial_open_retries < retries:
                        self.logger.error(f"Too many open serial attempts (maximum: {self.num_serial_open_retries}")
                        return None
        return self.serial_conn


class SerialToHttpHandler(http.server.BaseHTTPRequestHandler):
    server: SerialToHTTPServer

    def __init__(
            self,
            *args,
            retry_interval=DEFAULTS['retry_interval'],
            num_write_retries=DEFAULTS['num_write_retries'],
            logger_name=DEFAULTS['handler_logger_name'],
            http_content_type=DEFAULTS['http_content_type'],
            serial_encoding=DEFAULTS['serial_encoding'],
            http_encoding=DEFAULTS['http_encoding'],
            **kwargs):
        self.logger = logging.getLogger(logger_name)
        self.retry_interval = retry_interval
        self.num_write_retries = num_write_retries
        self.http_content_type = http_content_type
        self.serial_encoding = serial_encoding
        self.http_encoding = http_encoding

        super().__init__(*args, **kwargs)

    # called in socketserver.BaseServer.finish_request
    # self.RequestHandlerClass(request, client_address, self)
    # BaseHandlerClass.__init__:
    # def __init__(self, request, client_address, server):

    def _respond(self, data):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        # self.send_header("Server", "SerialToHttp")
        # self.send_header("Date", self.date_time_string())
        self.end_headers()
        self.wfile.write(data.encode(self.http_encoding))

    def do_GET(self):
        if not self.server.open_serial_conn():
            self.send_error(500, 'Failed to open serial connection')
        data = self.server.serial_conn.readline().decode(self.serial_encoding)
        self._respond(data)

    def do_POST(self):
        if not self.server.open_serial_conn():
            self.send_error(500, 'Failed to open serial connection')
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length).decode(self.http_encoding)
        retries = 0
        while True:
            try:
                self.server.serial_conn.write(post_data.encode(self.serial_encoding))
                data = self.server.serial_conn.readline().decode(self.serial_encoding)
                self._respond(data)
                break
            except Exception as e:
                self.logger.error(f"Failed to write to serial port: [{e.__class__.__name__}]{e}")
                retries += 1
                if retries > self.num_write_retries:
                    self.logger.error(f"Too many attempts  (maximum: {self.num_write_retries}")
                    self.send_error(500, "Failed to write/read data to/from serial port")
                    break
                self.server.open_serial_conn(force=True)



def run_serial_to_http(
        http_server_address=DEFAULTS['http_server_address'],
        http_server_port=DEFAULTS['http_server_port'],
        serial_device=DEFAULTS['serial_device'],
        baud_rate=DEFAULTS['baud_rate'],
        retry_interval=DEFAULTS['retry_interval'],
        num_write_retries=DEFAULTS['num_write_retries'],
        num_serial_open_retries=DEFAULTS['num_serial_open_retries'],
        http_content_type=DEFAULTS['http_content_type'],
        serial_encoding=DEFAULTS['serial_encoding'],
        http_encoding=DEFAULTS['http_encoding'],
):
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)

    with SerialToHTTPServer(
            server_address=(http_server_address, http_server_port),
            bind_and_activate=True,
            serial_device=serial_device,
            baud_rate=baud_rate,
            retry_interval=retry_interval,
            num_write_retries=num_write_retries,
            num_serial_open_retries=num_serial_open_retries,
            http_content_type=http_content_type,
            serial_encoding=serial_encoding,
            http_encoding=http_encoding,
            open_during_init=True
    ) as httpd:
        logging.info(f"Serving on port {http_server_port}")
        httpd.serve_forever()


def main(*args):
    parser = argparse.ArgumentParser(description='Run serial to HTTP')
    parser.add_argument('--http-server-address', type=str, default=DEFAULTS['http_server_address'], help='HTTP server address')
    parser.add_argument('--http-server-port', type=int, default=DEFAULTS['http_server_port'], help='HTTP server port')
    parser.add_argument('--serial-device', type=str, default=DEFAULTS['serial_device'], help='Serial port')
    parser.add_argument('--baud-rate', type=int, default=DEFAULTS['baud_rate'], help='Baud rate')
    parser.add_argument('--retry-interval', type=int, default=DEFAULTS['retry_interval'], help='Retry period in seconds')
    parser.add_argument('--num-write-retries', type=int, default=DEFAULTS['num_write_retries'], help='Number of write retries')
    parser.add_argument('--num-serial-open-retries', type=int, default=DEFAULTS['num_serial_open_retries'], help='Number of serial open retries')
    parser.add_argument('--http-content-type', type=str, default=DEFAULTS['http_content_type'], help='HTTP content type')
    parser.add_argument('--serial-encoding', type=str, default=DEFAULTS['serial_encoding'], help='Serial encoding')
    parser.add_argument('--http-encoding', type=str, default=DEFAULTS['http_encoding'], help='HTTP encoding')

    parsed_args = parser.parse_args(args)

    run_serial_to_http(
        http_server_address=parsed_args.http_server_address,
        http_server_port=parsed_args.http_server_port,
        serial_device=parsed_args.serial_device,
        baud_rate=parsed_args.baud_rate,
        retry_interval=parsed_args.retry_interval,
        num_write_retries=parsed_args.num_write_retries,
        num_serial_open_retries=parsed_args.num_serial_open_retries,
        http_content_type=parsed_args.http_content_type,
        serial_encoding=parsed_args.serial_encoding,
        http_encoding=parsed_args.http_encoding,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
