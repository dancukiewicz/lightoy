#!/usr/bin/env python3

import aiohttp
import aiohttp.web
import asyncio
import numpy
import os
import threading
import time

import color
import handlers.console
import handlers.input
from location_model import Spiral
from output import DummyOutput, SerialOutput
from session import Session


# TODO: command-line arg
HTTP_PORT = 8080
# TODO: command-line arg or autodetect
SERIAL_DEVICE = '/dev/ttyACM0'
SERIAL_BAUD = 115200
MAX_REFRESH_RATE = 200
# TODO: have Model class
NUM_LEDS = 300
# True to test out locally
NO_SERIAL = True


def render(session, location_model):
    """
    Returns a 3-by-n array representing the final color of each of the n LEDs.
    """
    t = session.get_time()
    t_diff = session.get_time_delta(t)
    inputs = session.input_processor.get_state(t)
    x = location_model.get_locations(session)

    effect = session.get_current_effect()

    output = effect.do_render(x, t, t_diff, inputs)
    numpy.clip(output, 0., 1., out=output)
    output = color.gamma_correct(output,
                                 session.global_params['gamma'].get_value())
    output *= session.global_params['brightness'].get_value()
    return output


def render_loop(session, location_model, output):
    while True:
        rendered = render(session, location_model)
        output.output(rendered)
        # Sleep to the next 1/MAX_REFRESH_RATE interval.
        refresh_interval = 1. / MAX_REFRESH_RATE
        sleep_time = refresh_interval - (time.time() % refresh_interval)
        if sleep_time == 0:
            sleep_time = refresh_interval
        time.sleep(sleep_time)


def get_template(template_name):
    template_filename = os.path.join(os.path.dirname(__file__), 'templates',
                                     '%s.html.mustache' % template_name)
    return open(template_filename, 'r').read()


async def init_app(event_loop, session):
    app = aiohttp.web.Application(loop=event_loop)
    app['session'] = session
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
    if NO_SERIAL:
        output = DummyOutput()
    else:
        output = SerialOutput(SERIAL_DEVICE, SERIAL_BAUD)
    session = Session(NUM_LEDS)
    # TODO: the location model should be configurable.
    location_model = Spiral(NUM_LEDS)
    render_thread = threading.Thread(target=render_loop,
                                     args=(session, location_model, output))
    render_thread.start()
    event_loop = asyncio.get_event_loop()
    web_app = event_loop.run_until_complete(init_app(event_loop, session))
    aiohttp.web.run_app(web_app)


if __name__ == "__main__":
    main()
