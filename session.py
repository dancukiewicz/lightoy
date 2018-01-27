"""
The Session class is used to hold the current state and configuration
of the lights.

This includes:
    * The current parameters.
    * Effect instances, which may have per-effect state.
    * Which effect is current.
    * The current input state.
    * TODO: how about time? Currently we hold start_time, but we may want to
      revamp that.
"""
import effects
import input
import params
import time


class Session(object):
    def __init__(self, num_leds):
        self.num_leds = num_leds
        self.effects = effects.create_effects(num_leds)
        self.cur_effect_name = sorted(self.effects.keys())[0]
        self.global_params = self._create_global_params()
        self.input_processor = input.InputProcessor()
        self.start_time = time.time()
        self.last_t = None

    def get_time(self):
        """Returns number of seconds since start of session."""
        if self.start_time is not None:
            return time.time() - self.start_time
        else:
            return 0.

    def get_time_delta(self, t):
        # Returns the number of second passed since the last time
        # get_time_delta() was called.
        if self.last_t:
            t_diff = t - self.last_t
        else:
            t_diff = 0.
        self.last_t = t
        return t

    def set_current_effect_name(self, effect_name):
        assert effect_name in self.effects.keys(), \
            "unknown effect: %s" % effect_name
        print("setting effect to: %s" % effect_name)
        self.cur_effect_name = effect_name

    def get_current_effect(self):
        return self.effects[self.cur_effect_name]

    def get_current_effect_name(self):
        return self.cur_effect_name



    @classmethod
    def _create_global_params(cls):
        # TODO: have consistent story of what global parameters are for.
        return {
            # total number of twists taken by the spiral
            # TODO: looks like we should have per-model params, or something
            # like that.
            'twists': params.Scalar(0., 30., 17.55),
            # adjusts the gamma curve:
            # adjusted_brightness = original_brightness ** gamma
            'gamma': params.Scalar(0., 100., 3.),
            # scales the brightness of the LEDs
            'brightness': params.Scalar(0., 1., 0.3),
        }

