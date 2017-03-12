#!/usr/bin/env python3

import aiohttp
import aiohttp.web
import asyncio
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
NUM_LEDS = 300
OUT_HEADER = bytes("head", 'utf-8')
# True to test out locally
NO_SERIAL = False


# time at which the server was started
START_TIME = None


def get_server_time():
    global START_TIME
    return time.time() - START_TIME


# Defines  a parameter that goes into an effect
class Slider:
    def __init__(self, name, min_value, max_value, default_value):
        self.min_value = min_value
        self.max_value = max_value
        self.name = name
        self.default_value = default_value
        self.value = default_value

    def set_value(self, value):
        if value < self.min_value or value > self.max_value:
            raise Exception("Value given (%f) can't exceed bounds [%f, %f]" %
                            (value, self.min_value, self.max_value))
        self.value = value

    def get_value(self):
        return self.value


class EffectInfo:
    def __init__(self, name, effect, sliders=None):
        self.name = name
        self.effect = effect
        self.sliders = sliders or []


# effect name => (effect, list of sliders)
# TODO: effect name => value
EFFECT_LIST = [
    EffectInfo('wavy', effects.WavyEffect(NUM_LEDS)),
    EffectInfo('wander', effects.Wander(NUM_LEDS),
               [Slider('speed', 0, 2, 0.3)]),
    EffectInfo('march', effects.March(NUM_LEDS)),
    EffectInfo('wipe', effects.VerticalWipe(NUM_LEDS)),
]

EFFECTS = {effect.name: effect for effect in EFFECT_LIST}

CURRENT_EFFECT = 'wipe'

GLOBAL_SLIDERS = [
    # total number of twists taken by the spiral
    Slider('twists',     0., 30., 17.55),
    Slider('brightness', 0.,  1.,  1.),
]


class Sliders:
    # effect name => slider name => slider
    effect_sliders = {}
    # slider name => slider
    global_sliders = {}

    def __init__(self, effects, global_sliders):
        for effect_name, effect_info in effects.items():
            self.effect_sliders[effect_name] = {
                slider.name: slider for slider in effect_info.sliders
            }
        self.global_sliders = {
            slider.name: slider for slider in global_sliders
        }

# current slider values

SLIDERS = Sliders(EFFECTS, GLOBAL_SLIDERS)

INPUT_PROCESSOR = input.InputProcessor()


# TODO: split out into module
def get_locations():
    """Returns a 3-by-NUM_LEDS array representing the x,y,z positions of the
    LEDs. Each dimension ranges from 0 to 1.
    X: right, y: out from viewer, z: up
    """
    # orientation of spiral, looking from the top
    # 1 for counterclockwise, -1 for clockwise
    direction = -1

    twists = SLIDERS.global_sliders['twists'].get_value()
    # angle in x-y plane swept between two consequent LEDs
    theta_per_led = 2. * numpy.pi * twists / NUM_LEDS
    thetas = numpy.array(range(NUM_LEDS)) * theta_per_led
    locations = numpy.zeros((3, NUM_LEDS))
    # X
    locations[0, :] = numpy.cos(thetas * direction)
    # Y
    locations[1, :] = numpy.sin(thetas * direction)
    # Z
    locations[2, :] = numpy.linspace(-1., 1., NUM_LEDS)
    return locations


def render():
    """
    Returns a 3-by-n array representing the final color of each of the n LEDs.
    """
    t = get_server_time()
    inputs = INPUT_PROCESSOR.get_state(t)
    x = get_locations()

    effect = EFFECTS[CURRENT_EFFECT]
    # TODO: naming becomes awkward here
    output = effect.effect.render(x, t, inputs,
                                  SLIDERS.effect_sliders[effect.name])
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
    INPUT_PROCESSOR.on_touch_start(touches, get_server_time())
    print("touch start:", msg)
    return pos(touches)


async def handle_touch_move(msg):
    touches = msg['touches']
    INPUT_PROCESSOR.on_touch_move(touches, get_server_time())
    return pos(touches)

async def handle_touch_end(msg):
    INPUT_PROCESSOR.on_touch_end(get_server_time())
    print("touch end:", msg)
    return pos([])


async def handle_touch_cancel(msg):
    INPUT_PROCESSOR.on_touch_end(get_server_time())
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

    cur_effect = {'name': CURRENT_EFFECT}

    effect = EFFECTS[CURRENT_EFFECT]

    def get_slider_data(slider):
        return {
            'name': slider.name,
            'min_value': slider.min_value,
            'max_value': slider.max_value,
            'default_value': slider.default_value,
            'cur_value': slider.get_value(),
        }

    effect_slider_data = [get_slider_data(slider)
        for slider_name, slider in SLIDERS.effect_sliders[effect.name].items()]
    global_slider_data = [get_slider_data(slider)
        for slider_name, slider in SLIDERS.global_sliders.items()]

    other_effects = []
    for effect_name in EFFECTS:
        if effect_name != CURRENT_EFFECT:
            other_effects.append({'name': effect_name})

    text = pystache.render(template, {
        'current_effect': cur_effect,
        'other_effects': other_effects,
        'effect_sliders': effect_slider_data,
        'global_sliders': global_slider_data
        })
    return aiohttp.web.Response(text=text,
                                headers={'content-type': 'text/html'})


async def handle_effect_request(request):
    global CURRENT_EFFECT
    print(request)
    data = await request.post()
    CURRENT_EFFECT = data['effect']
    return aiohttp.web.Response(status=302,
                                headers={'Location': '/console'})


async def handle_sliders_request(request):
    data = await request.post()
    effect_name = data['effect']
    if effect_name == 'global':
        sliders = SLIDERS.global_sliders
    else:
        sliders = SLIDERS.effect_sliders[effect_name]

    for slider_name, slider in sliders.items():
        if slider_name in data:
            value = float(data[slider_name])
            print("setting slider: %s to %f" % (slider.name, value))
            slider.set_value(value)
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
    global START_TIME
    START_TIME = time.time()
    render_thread = threading.Thread(target=render_loop)
    render_thread.start()
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init(loop))
    aiohttp.web.run_app(app)


if __name__ == "__main__":
    main()
