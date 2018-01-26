#!/usr/bin/env python3

import aiohttp
import aiohttp.web
import asyncio
import numpy
import os
import serial
import threading
import time

import color
import effects
import handlers.console
import handlers.input
import input
import params
import shared

# TODO: command-line arg
HTTP_PORT = 8080
# TODO: command-line arg or autodetect
SERIAL_DEVICE = '/dev/ttyACM0'
SERIAL_BAUD = 115200
REFRESH_RATE = 200
# TODO: command-line arg
NUM_LEDS = 300
OUT_HEADER = bytes("head", 'utf-8')
# True to test out locally
NO_SERIAL = False


def get_server_time():
    if shared.start_time is not None:
        return time.time() - shared.start_time
    else:
        return 0.


shared.effects = effects.create_effects(NUM_LEDS)
shared.cur_effect_name = "Cylinder"


def get_current_effect():
    return shared.cur_effect_name


def set_current_effect(effect_name):
    assert effect_name in shared.effects.keys(), \
        "unknown effect: %s" % effect_name
    print("setting effect to: %s" % effect_name)
    shared.cur_effect_name = effect_name


shared.global_params = {
    # total number of twists taken by the spiral
    'twists': params.Scalar(0., 30., 17.55),
    # adjusts the gamma curve: adjusted_brightness = orig_brightness ** gamma
    'gamma': params.Scalar(0., 100., 3.),
    # scales the brightness of the LEDs
    'brightness': params.Scalar(0., 1., 0.3),

}

shared.input_processor = input.InputProcessor()


# TODO: split out into module
def get_locations():
    """Returns a 3-by-NUM_LEDS array representing the x,y,z positions of the
    LEDs. Each dimension ranges from 0 to 1.
    X: right, y: out from viewer, z: up
    """
    # orientation of spiral, looking from the top
    # 1 for counterclockwise, -1 for clockwise
    direction = -1

    twists = shared.global_params['twists'].get_value()
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
    if shared.last_t is not None:
        t_diff = t - shared.last_t
    else:
        t_diff = t
    shared.render_time_history.append(t_diff)
    shared.render_time_history = shared.render_time_history[-30:]

    shared.last_t = t
    inputs = shared.input_processor.get_state(t)
    x = get_locations()

    effect = shared.effects[get_current_effect()]

    output = effect.do_render(x, t, t_diff, inputs)
    numpy.clip(output, 0., 1., out=output)
    output = color.gamma_correct(output,
                                 shared.global_params['gamma'].get_value())
    output *= shared.global_params['brightness'].get_value()
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
        # TODO: huh? what's that mean?
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
        refresh_interval = 1. / REFRESH_RATE
        sleep_time = refresh_interval - (time.time() % refresh_interval)
        if sleep_time == 0:
            sleep_time = refresh_interval
        time.sleep(sleep_time)


def get_template(template_name):
    template_filename = os.path.join(os.path.dirname(__file__), 'templates',
                                     '%s.html.mustache' % template_name)
    return open(template_filename, 'r').read()


async def init_app(event_loop):
    app = aiohttp.web.Application(loop=event_loop)
    app.router.add_get('/', handlers.input.handle_touchpad_request)
    app.router.add_get('/console', handlers.console.handle_console_request)
    app.router.add_post('/console/effect',
                        handlers.console.handle_change_effect_request)
    app.router.add_post('/console/params',
                        handlers.console.handle_update_params_request)
    app.router.add_get('/console_ws', handlers.console.handle_websocket_request)
    app.router.add_get('/touch_ws', handlers.input.handle_websocket_request)
    app.router.add_static('/static', 'static', name='static')
    return app


def main():
    shared.start_time = time.time()
    render_thread = threading.Thread(target=render_loop)
    render_thread.start()
    event_loop = asyncio.get_event_loop()
    web_app = event_loop.run_until_complete(init_app(event_loop))
    aiohttp.web.run_app(web_app)


if __name__ == "__main__":
    main()
