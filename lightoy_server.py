#!/usr/bin/env python3

import aiohttp
import aiohttp.web
import asyncio
from collections import namedtuple
import effects
import input
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
NUM_LEDS = 250
OUT_HEADER = bytes("head", 'utf-8')
# True to test out locally
NO_SERIAL = True


# time at which the server was started
start_time = None


def get_server_time():
    global start_time
    return time.time() - start_time

# Defines  a parameter that goes into an effect
Slider = namedtuple('Slider', ['name', 'min_value', 'max_value',
                               'default_value'])


class EffectInfo:
    def __init__(self, effect, sliders):
        self.effect = effect
        self.sliders = sliders
        self.slider_values = {
            slider.name: slider.default_value
            for slider in sliders}

    def set_slider(self, name, value):
        self.slider_values[name] = value

# effect name => (effect, list of sliders)
EFFECTS = {
    'wavy': EffectInfo(effects.WavyEffect(NUM_LEDS), []),
    'wander': EffectInfo(effects.Wander(NUM_LEDS),
                         [Slider('speed', 0, 2, 0.3)])
}

current_effect = 'wander'


input_processor = input.InputProcessor()


def render():
    """
    Returns a 3-by-n array representing the final color of each of the n LEDs.
    """
    t = get_server_time()
    inputs = input_processor.get_state(t)
    x = numpy.linspace(0., 1., NUM_LEDS).reshape((1, -1))
    effect = EFFECTS[current_effect]
    # TODO: naming becomes awkward here
    output = effect.effect.render(x, t, inputs, effect.slider_values)
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
        # The LED at the end is at x=0, which is simply an artifact of how I
        # laid them out now.
        # TODO: make the color order configurable
        r, g, b = output[:, NUM_LEDS - led - 1]
        out_data.append(int(g*255))
        out_data.append(int(r*255))
        out_data.append(int(b*255))
    return out_data


def render_loop():
    if NO_SERIAL:
        ser = None
    else:
        ser = serial.Serial(SERIAL_DEVICE, SERIAL_BAUD, timeout=None,
                            write_timeout=None, xonxoff=False,
                            rtscts=False, dsrdtr=False, inter_byte_timeout=None)
    while True:
        # Render the frame and send it out to the Teensy.
        out_data = get_out_data()
        if not NO_SERIAL:
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


def pos(touches):
    return {'pos': touches}


async def handle_touch_start(msg):
    touches = msg['touches']
    input_processor.on_touch_start(touches, get_server_time())
    print("touch start:", msg)
    return pos(touches)


async def handle_touch_move(msg):
    touches = msg['touches']
    input_processor.on_touch_move(touches, get_server_time())
    return pos(touches)

async def handle_touch_end(msg):
    input_processor.on_touch_end(get_server_time())
    print("touch end:", msg)
    return pos([])


async def handle_touch_cancel(msg):
    input_processor.on_touch_end(get_server_time())
    print("touch end:", msg)
    return pos([])


async def handle_touchpad_request(request):
    template_filename = os.path.join(os.path.dirname(__file__), 'templates',
                                     'touchpad.html.mustache')
    template = open(template_filename, 'r').read()
    text = pystache.render(template, {})
    return aiohttp.web.Response(text=text,
                                headers={'content-type': 'text/html'})


async def handle_console_request(request):
    template_filename = os.path.join(os.path.dirname(__file__), 'templates',
                                     'console.html.mustache')
    template = open(template_filename, 'r').read()

    cur_effect = {'name': current_effect}

    effect = EFFECTS[current_effect]
    slider_data = [{
        'name': slider.name,
        'min_value': slider.min_value,
        'max_value': slider.max_value,
        'default_value': slider.default_value,
        'cur_value': effect.slider_values[slider.name]
    } for slider in effect.sliders]

    other_effects = []
    for effect_name in EFFECTS:
        if effect_name != current_effect:
            other_effects.append({'name': effect_name})

    text = pystache.render(template, {
        'current_effect': cur_effect,
        'other_effects': other_effects,
        'sliders': slider_data,
        })
    return aiohttp.web.Response(text=text,
                                headers={'content-type': 'text/html'})


async def handle_effect_request(request):
    global current_effect
    print(request)
    data = await request.post()
    current_effect = data['effect']
    return aiohttp.web.Response(status=302,
                                headers={'Location': '/console'})


async def handle_sliders_request(request):
    data = await request.post()
    effect = EFFECTS[current_effect]
    for slider in  effect.sliders:
        if slider.name in data:
            value = float(data[slider.name])
            print("setting slider: %s to %f" % (slider.name, value))
            effect.set_slider(slider.name, value)
    return aiohttp.web.Response(status=302,
                                headers={'Location': '/console'})


async def handle_websocket_request(request):
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
    app.router.add_get('/', handle_touchpad_request)
    app.router.add_get('/console', handle_console_request)
    app.router.add_post('/console/effect', handle_effect_request)
    app.router.add_post('/console/sliders', handle_sliders_request)
    app.router.add_get('/ws', handle_websocket_request)
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
