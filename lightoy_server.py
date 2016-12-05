#!/usr/bin/env python3

import aiohttp
import aiohttp.web
import asyncio
import json
import os
import pystache


# TODO: command-line arg
HTTP_PORT = 8080


# each handler should return its response
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
    print("touch start:", msg)
    return pos(msg['touches'])


async def handle_touch_move(msg):
    #print("touch move:", msg)
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
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init(loop))
    aiohttp.web.run_app(app)


if __name__ == "__main__":
    main()
