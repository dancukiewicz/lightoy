import aiohttp
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