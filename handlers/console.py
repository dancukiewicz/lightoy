import aiohttp
import json
import pystache

import lightoy_server
import params
import shared


async def handle_console_request(request):
    template = lightoy_server.get_template('console')
    cur_effect_name = lightoy_server.get_current_effect()
    current_effect = shared.effects[cur_effect_name]

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

    effect_param_data = get_param_data(current_effect.params)
    global_param_data = get_param_data(shared.global_params)

    other_effects = [
        {'name': effect_name}
        for effect_name in shared.effects.keys()
        if effect_name != cur_effect_name]

    text = pystache.render(template, {
        'current_effect': {
            'name': cur_effect_name
            },
        'other_effects': other_effects,
        'effect_params': effect_param_data,
        'global_params': global_param_data
        })
    return aiohttp.web.Response(text=text,
                                headers={'content-type': 'text/html'})


async def handle_change_effect_request(request):
    data = await request.post()
    lightoy_server.set_current_effect(data['effect'])
    return aiohttp.web.Response(status=302,
                                headers={'Location': '/console'})


async def handle_update_params_request(request):
    data = await request.post()
    effect_name = data['effect']
    # TODO: magic string, but breaking out into a constant wouldn't make sense.
    if effect_name == 'global':
        param_dict = shared.global_params
    else:
        param_dict = shared.effects[effect_name].params

    for param_name, param in param_dict.items():
        if param_name in data:
            assert issubclass(param.__class__, params.Scalar), \
                "non-scalar params unsupported"
            value = float(data[param_name])
            print("setting param: %s to %f" % (param_name, value))
            param.set_value(value)
    return aiohttp.web.Response(status=302,
                                headers={'Location': '/console'})


# Each handler should return its response.
# TODO: code duplication with the input.py ws message handler
async def handle_websocket_message(msg):
    handlers = {
        'sliderUpdate': handle_slider_update,
    }
    event = msg['ev']
    if event in handlers:
        return await handlers[event](msg)
    else:
        # TODO: logging
        print("Unrecognized event:", event, "in message:", msg)
        return None


async def handle_slider_update(msg):
    # TODO: this and the static UI should update the parameters using the
    # same pathway
    name = msg['name']
    value = msg['value']

    cur_effect_name = lightoy_server.get_current_effect()
    current_effect = shared.effects[cur_effect_name]

    if name in current_effect.params:
        current_effect.params[name].set_value(value)
    else:
        # TODO: logging
        print("Unrecognized param:", name)


async def handle_websocket_request(request):
    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                response = await handle_websocket_message(json.loads(msg.data))
                if response is not None:
                    ws.send_json(response)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())
