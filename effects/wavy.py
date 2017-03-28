import numpy

from effects.effect import Effect
import params


class Wavy(Effect):
    def __init__(self, n_leds):
        self.params = {'periods': params.RandomArray(n_leds)}

    @classmethod
    def render(cls, x, t, inputs, param):
        # TODO: params
        n = x.shape[1]
        # Default: just make everything red, with a bit of a wavy effect.
        brightness_modulation = (
            numpy.sin(t * 10 * param['periods']))
        brightness = ((0.8 - 0.1 * inputs.fade)
                      + (0.2 + 0.1 * inputs.fade) * brightness_modulation)
        pos_mask = numpy.sin((x[0, :] - inputs.focus_x) * 5)**8

        h = (0.5 + 0.5 * numpy.sin(inputs.focus_y * 2)) * numpy.ones((1, n))
        s = 0.8 * numpy.ones((1, n))
        v = ((0.25 + 0.75 * inputs.fade) *
             numpy.multiply(brightness, pos_mask))
        hsv = numpy.vstack([h, s, v])
        return cls.hsv_to_rgb(hsv)
