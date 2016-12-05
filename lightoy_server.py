#!/usr/bin/env python3

import aiohttp
import aiohttp.web
import asyncio
import json
import os
import pystache


# TODO: command-line arg
HTTP_PORT = 8080


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
                print("message: " + msg.data)
                ws.send_str(msg.data + '/answer')
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

# import aiohttp.web
# import aiohttp.log
# import pathlib

# async def hello(websocket, path):
#     name = await websocket.recv()
#     print("< {}".format(name))
#
#     greeting = "Hello {}!".format(name)
#     await websocket.send(greeting)
#     print("> {}".format(greeting))
#
# app = aiohttp.web.Application()
# app.router.add_static('/',
#                       pathlib.Path(pathlib.Path(__file__).parent, 'static'),
#                       show_index=True)
# loop = app.loop
# handler = app.make_handler(access_log=aiohttp.log.access_logger,
#                            host='0.0.0.0',
#                            port=HTTP_PORT,
#                            backlog=128)
# loop.run_until_complete()


# aiohttp.web.run_app(app)

#start_server = websockets.serve(hello, 'localhost', 8765)


#asyncio.get_event_loop().run_until_complete(start_server)
#asyncio.get_event_loop().run_forever()
