#!/usr/bin/env python3

import aiohttp
import aiohttp.web
import asyncio
import json
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


# This is accessed from both the web and render threads.
cur_touches = []

def render():

    touches = cur_touches
    touch_val = 0
    if len(touches) > 0:
        touch_val = touches[0]['x']

    brightness = int(touch_val * 256)
    if brightness > 255:
        brightness = 255
    elif brightness < 0:
        brightness = 0
    
    return str(brightness) + "."

    #touches = cur_touches
    #if len(touches) > 0:
    #    return "H"
    #else:
    #    return "L"


def render_loop():
    ser = serial.Serial(SERIAL_DEVICE, SERIAL_BAUD, timeout=None,
                        write_timeout=None, xonxoff=False,
                        rtscts=False, dsrdtr=False, inter_byte_timeout=None)
    while True:
        # Render the frame and send it out to the Teensy.
        b = render()
        ser.write(bytes(b, 'utf-8'))
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
    render_thread = threading.Thread(target=render_loop)
    render_thread.start()
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init(loop))
    aiohttp.web.run_app(app)


if __name__ == "__main__":
    main()
