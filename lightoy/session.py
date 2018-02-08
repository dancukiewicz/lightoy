import time

import lightoy.effects
import lightoy.input
import lightoy.params


class Session(object):
    """
    The Session class is used to hold the current state and configuration
    of the lights.

    This includes:
        * The current parameters.
        * Effect instances, which may have per-effect state.
        * Which effect is current.
        * The current input state.
        * Timing-related information.
    """
    def __init__(self, num_leds):
        self.num_leds = num_leds
        self.effects = lightoy.effects.create_effects(num_leds)
        self.cur_effect_name = sorted(self.effects.keys())[0]
        self.global_params = self._create_global_params()
        self.input_processor = lightoy.input.InputProcessor()
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
        return t_diff

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
            # TODO: looks like we should have per-model params.
            # Total number of twists taken by the spiral.
            'twists': lightoy.params.Scalar(0., 30., 17.55),
            # adjusts the gamma curve:
            # adjusted_brightness = original_brightness ** gamma
            'gamma': lightoy.params.Scalar(0., 100., 3.),
            # scales the brightness of the LEDs
            'brightness': lightoy.params.Scalar(0., 1., 0.3),
        }

