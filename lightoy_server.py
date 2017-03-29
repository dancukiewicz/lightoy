#!/usr/bin/env python3

import aiohttp
import aiohttp.web
import asyncio
import json
import numpy
import os
import pystache
import serial
import threading
import time

import effects
import input
import params

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
# the last time the lights were rendered
LAST_T = None
T_DIFF_HISTORY = []


def get_server_time():
    global START_TIME
    return time.time() - START_TIME


def get_effects():
    """Returns an {effect name => initialized effect} dict.
    """
    all_effect_classes = effects.Effect.__subclasses__()
    return {
        effect_class.__name__: effect_class(NUM_LEDS)
        for effect_class in all_effect_classes
        }

EFFECTS = get_effects()

CURRENT_EFFECT = 'VerticalWipe'

GLOBAL_PARAMS = {
    # total number of twists taken by the spiral
    'twists': params.Scalar(0., 30., 17.55),
    # scales the brightness of the LEDs
    'brightness': params.Scalar(0., 1., 1.),
}

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

    twists = GLOBAL_PARAMS['twists'].get_value()
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
    global LAST_T, T_DIFF_HISTORY
    t = get_server_time()
    if LAST_T is not None:
        t_diff = t - LAST_T
    else:
        t_diff = t
    T_DIFF_HISTORY.append(t_diff)
    T_DIFF_HISTORY = T_DIFF_HISTORY[-30:]

    LAST_T = t
    inputs = INPUT_PROCESSOR.get_state(t)
    x = get_locations()

    effect = EFFECTS[CURRENT_EFFECT]

    output = effect.do_render(x, t, t_diff, inputs)
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

    def format_param_data(param, param_name):
        return {
            'name': param_name,
            'min_value': param.min_value,
            'max_value': param.max_value,
            'default_value': param.default_value,
            'cur_value': param.get_value(),
        }

    def get_param_data(param_dict):
        """param_dict: name => param object dict

        Returns: A list of corresponding formatting dicts
        """
        return [
            format_param_data(param, param_name)
            for param_name, param in param_dict.items()
            # for now we only render scalar params
            if issubclass(param.__class__, params.Scalar)
            ]

    effect_param_data = get_param_data(effect.params)
    global_param_data = get_param_data(GLOBAL_PARAMS)

    other_effects = [
        {'name': effect_name}
        for effect_name in EFFECTS.keys()
        if effect_name != CURRENT_EFFECT]

    text = pystache.render(template, {
        'current_effect': cur_effect,
        'other_effects': other_effects,
        'effect_params': effect_param_data,
        'global_params': global_param_data
        })
    return aiohttp.web.Response(text=text,
                                headers={'content-type': 'text/html'})


async def handle_change_effect_request(request):
    global CURRENT_EFFECT
    print(request)
    data = await request.post()
    CURRENT_EFFECT = data['effect']
    return aiohttp.web.Response(status=302,
                                headers={'Location': '/console'})


async def handle_update_params_request(request):
    data = await request.post()
    effect_name = data['effect']
    # TODO: magic string, but breaking out into a constant wouldn't make sense.
    if effect_name == 'global':
        param_dict = GLOBAL_PARAMS
    else:
        param_dict = EFFECTS[effect_name].params

    for param_name, param in param_dict.items():
        if param_name in data:
            assert issubclass(param.__class__, params.Scalar), \
                "non-scalar params unsupported"
            value = float(data[param_name])
            print("setting param: %s to %f" % (param_name, value))
            param.set_value(value)
    return aiohttp.web.Response(status=302,
                                headers={'Location': '/console'})


async def handle_input_websocket_request(request):
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


async def handle_console_websocket_request(request):
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
    app.router.add_post('/console/effect', handle_change_effect_request)
    app.router.add_post('/console/params', handle_update_params_request)
    app.router.add_get('/input_ws', handle_input_websocket_request)
    app.router.add_get('/console_ws', handle_console_websocket_request)
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
