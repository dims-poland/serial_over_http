import logging

NAME = 'Serial over HTTP Server'
AUTHOR = 'DIMS'
VERSION = '0.0.1'

DEFAULTS = dict(
    serial_device='COM6',
    serial_timeout=1,
    http_server_address='127.0.0.1',
    http_server_port=8888,
    baud_rate=9600,
    open_interval=5,
    write_retry_interval=5,
    open_retry_interval=5,
    num_write_retries=5,
    num_serial_open_retries=100,
    transcode=False,
    http_content_type='application/octet-stream',
    # http_content_type='text/plain',
    serial_encoding='ISO-8859-1',
    http_encoding='ISO-8859-1',
    open_during_init=True,
    server_logger_name='SerialOverHttpServer',
    handler_logger_name='SerialOverHttpHandler',
    token_variable='token',
    tokens=tuple(),
    log_level=logging.INFO,
    log_file=None,
    config_file_name=None
)