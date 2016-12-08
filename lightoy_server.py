#!/usr/bin/env python3

import aiohttp
import aiohttp.web
import asyncio
import effects
import json
import numpy
import os
import pystache
import serial
import threading
import time


# TODO: command-line arg
HTTP_PORT = 8080
# TODO: command-line arg or autodetect
SERIAL_DEVICE = '/dev/ttyACM0'
SERIAL_BAUD = 115200
REFRESH_RATE = 200
NUM_LEDS = 50
OUT_HEADER = bytes("head", 'utf-8')

# time at which the server was started
start_time = None

# This is accessed from both the web and render threads.
cur_touches = []

# Fade in/out effect; varies from 0 to 1.
fade = 0.

x_touch_val = 0
y_touch_val = 0

# a list of the previous
TOUCH_HIST_LENGTH = 3
touch_history = numpy.zeros((TOUCH_HIST_LENGTH, 2))

EFFECTS = [
    effects.WavyEffect(NUM_LEDS)
]


def render():
    """
    Returns a 3-by-n array representing the final color of each of the n LEDs.
    """
    # TODO: refactor the whole input thing
    touches = cur_touches
    global x_touch_val
    global y_touch_val
    global fade
    global touch_history
    if len(touches) > 0:
        touch = touches[0]
        x_touch_val = touch['x']
        x_touch_val = numpy.clip(x_touch_val, 0.0, 1.0)
        y_touch_val = touch['y']
        y_touch_val = numpy.clip(y_touch_val, 0.0, 1.0)
        global touch_history
        touch_history = numpy.roll(touch_history, 1, 0)
        touch_history[0, 0] = x_touch_val
        touch_history[0, 1] = y_touch_val
        fade += 0.01
    else:
        fade -= 0.002

    fade = numpy.clip(fade, 0.0, 1.0)

    x = numpy.linspace(0, 1, NUM_LEDS).reshape((1, -1))
    global start_time
    t = time.time() - start_time

    output = numpy.zeros((3, NUM_LEDS))
    for effect in EFFECTS:
        output += effect.render(x, t)
    numpy.clip(output, 0., 1., out=output)
    return output


def get_out_data():
    """
    Returns a byte buffer representing the data that will be sent over serial
        for this frame.
    """
    output = render()
    out_data = bytearray(OUT_HEADER)
    for led in range(NUM_LEDS):
        r, g, b = output[:, led]
        out_data.append(int(g*255))
        out_data.append(int(r*255))
        out_data.append(int(b*255))
    return out_data


def render_loop():
    ser = serial.Serial(SERIAL_DEVICE, SERIAL_BAUD, timeout=None,
                        write_timeout=None, xonxoff=False,
                        rtscts=False, dsrdtr=False, inter_byte_timeout=None)
    while True:
        # Render the frame and send it out to the Teensy.
        out_data = get_out_data()
        ser.write(out_data)
        ser.flush()
        # Sleep to the next 1/REFRESH_RATE interval.
        refresh_interval = 1 / REFRESH_RATE
        sleep_time = refresh_interval - (time.time() % refresh_interval)
        if sleep_time == 0:
            sleep_time = refresh_interval
        time.sleep(sleep_time)


# Each handler should return its response.
async def handle_message(msg):
    handlers = {
        'touchstart': handle_touch_start,
        'touchmove': handle_touch_move,
        'touchend': handle_touch_end,
        'touchcancel': handle_touch_cancel
    }
    event = msg['ev']
    if event in handlers:
        return await handlers[event](msg)
    else:
        # TODO: logging
        print("Unrecognized event:", event, "in message:", msg)
        return None


# TODO: pos() does two very different things
def pos(touches):
    global cur_touches
    cur_touches = touches
    return {'pos': touches}


async def handle_touch_start(msg):
    print("touch start:", msg)
    return pos(msg['touches'])


async def handle_touch_move(msg):
    return pos(msg['touches'])


async def handle_touch_end(msg):
    print("touch end:", msg)
    return pos([])


async def handle_touch_cancel(msg):
    print("touch cancel:", msg)
    return pos([])


async def handle_main(request):
    template_filename = os.path.join(os.path.dirname(__file__), 'templates',
                                     'main.html.mustache')
    template = open(template_filename, 'r').read()
    text = pystache.render(template, {})
    return aiohttp.web.Response(text=text,
                                headers={'content-type': 'text/html'})


async def handle_websocket(request):
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                response = await handle_message(json.loads(msg.data))
                if response is not None:
                    ws.send_json(response)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())


async def init(loop):
    app = aiohttp.web.Application(loop=loop)
    app.router.add_get('/', handle_main)
    app.router.add_get('/ws', handle_websocket)
    app.router.add_static('/static', 'static', name='static')
    return app


def main():
    global start_time
    start_time = time.time()
    render_thread = threading.Thread(target=render_loop)
    render_thread.start()
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init(loop))
    aiohttp.web.run_app(app)


if __name__ == "__main__":
    main()
