import aiohttp
import json
import os
import pystache
import shared

import lightoy_server

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
    shared.input_processor.on_touch_start(
        touches, lightoy_server.get_server_time())
    print("touch start:", msg)
    return pos(touches)


async def handle_touch_move(msg):
    touches = msg['touches']
    shared.input_processor.on_touch_move(
        touches, lightoy_server.get_server_time())
    return pos(touches)


async def handle_touch_end(msg):
    shared.input_processor.on_touch_end(lightoy_server.get_server_time())
    print("touch end:", msg)
    return pos([])


async def handle_touch_cancel(msg):
    shared.input_processor.on_touch_end(lightoy_server.get_server_time())
    print("touch end:", msg)
    return pos([])


async def handle_touchpad_request(request):
    template = lightoy_server.get_template('touchpad')
    text = pystache.render(template, {})
    return aiohttp.web.Response(text=text,
                                headers={'content-type': 'text/html'})


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
