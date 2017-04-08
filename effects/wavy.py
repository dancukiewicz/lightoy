import numpy

import color
from effects.effect import Effect
import params


class Wavy(Effect):
    def init_params(self):
        return {'periods': params.RandomArray(self.n_leds)}

    @classmethod
    def render(cls, x, t, t_diff, inputs, param, state):
        # TODO: break out more things into params
        n = x.shape[1]
        # Default: just make everything red, with a bit of a wavy effect.
        periods = param['periods'].get_value()
        brightness_modulation = numpy.sin(t * 10 * periods)
        brightness = ((0.8 - 0.1 * inputs.fade)
                      + (0.2 + 0.1 * inputs.fade) * brightness_modulation)
        pos_mask = numpy.sin((x[0, :] - inputs.focus_x) * 5)**8
        # avoid cases of light on the edge flickering on and off noticeably
        # because they alternate between, ex. (0,0,0) and (0,0,1)
        # unfortunately the light output (or at least the perception of it)
        # is not linear w.r.t. the brightness sent over
        pos_mask[pos_mask < 0.17] = 0.

        h = (0.5 + 0.5 * numpy.sin(inputs.focus_y * 2)) * numpy.ones((1, n))
        s = 0.8 * numpy.ones((1, n))
        v = ((0.25 + 0.75 * inputs.fade) *
             numpy.multiply(brightness, pos_mask))
        hsv = numpy.vstack([h, s, v])
        return color.hsv_to_rgb(hsv)
