# time at which the server was started (sec)
start_time = None
# the last time the lights were rendered (sec)
last_t = None
cur_effect_name = None
# (effect name => effect) dict
effects = None
# (param name => param) dict
global_params = None
# list of the last N render times (sec)
render_time_history = []
# input.InputProcessor instance
input_processor = None
