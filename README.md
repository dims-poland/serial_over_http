# Serial over HTTP server
This script creates an HTTP server that writes data received by POST request to a serial port/character device.
Data received from the serial port/character device is sent back to the client as a response the request.

For testing use `socat` to create a virtual serial port:

```bash
socat -d -d pty,raw,echo=0 pty,raw,echo=0
```