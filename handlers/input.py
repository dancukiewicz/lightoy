import aiohttp
import json
import pystache

import lightoy_server


async def handle_touchpad_request(request):
    template = lightoy_server.get_template('touchpad')
    text = pystache.render(template, {})
    return aiohttp.web.Response(text=text,
                                headers={'content-type': 'text/html'})


# Each handler should return its response.
async def handle_websocket_message(msg, session):
    handlers = {
        'touchstart': handle_touch_start,
        'touchmove': handle_touch_move,
        'touchend': handle_touch_end,
        'touchcancel': handle_touch_cancel
    }
    event = msg['ev']
    if event in handlers:
        return await handlers[event](msg, session)
    else:
        # TODO: logging
        print("Unrecognized event:", event, "in message:", msg)
        return None


def pos(touches):
    return {'pos': touches}


async def handle_touch_start(msg, session):
    touches = msg['touches']
    session.input_processor.on_touch_start(touches, session.get_time())
    print("touch start:", msg)
    return pos(touches)


async def handle_touch_move(msg, session):
    touches = msg['touches']
    session.input_processor.on_touch_move(
        touches, session.get_time())
    return pos(touches)


async def handle_touch_end(msg, session):
    session.input_processor.on_touch_end(session.get_time())
    print("touch end:", msg)
    return pos([])


async def handle_touch_cancel(msg, session):
    session.input_processor.on_touch_end(session.get_time())
    print("touch end:", msg)
    return pos([])


async def handle_websocket_request(request):
    session = request.app['session']
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                response = await handle_websocket_message(
                    json.loads(msg.data), session)
                if response is not None:
                    ws.send_json(response)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())
