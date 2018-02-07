# Lightoy

...is a tool for creating, running and interacting with effects on RGB LED arrays, like those using the WS2811 chip. Here's an example:

TODO: upload to youtube

It runs a webserver (by default on port 8080), which exposes the following endpoints:

* `/`: Returns a console page, which lets the user change effects and tweak parameters that change how the effects are rendered.
* `/touch`: Returns a blank page, which responds to touch events. These events are then sent to a server via a websocket connection, and effects can use these touch events when rendering.
 
In order to drive the array, the server sends the colors of each light over via a serial interface. I used a Teensy 3.2 board, loaded with the included Arduino program (`firmware/teensy.ino`), to listen on its USB UART and drive the lights using the OctoWS2811 library.

## Running

Requires Python 3 and the `aiohttp`, `click` and `numpy` packages. To run:

```python
python lightoy_server.py {SERIAL_DEVICE} 
```

where `{SERIAL_DEVICE}` is the device name of the Teensy's USB UART. For me, in Ubuntu 16.04, this shows up as `dev/ttyACM0`.
