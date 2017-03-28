import numpy

from effect import Effect


class VerticalWipe(Effect):
    @classmethod
    def render(cls, X, t, inputs, slider_values):
        x = X[0, :]
        brightness = 0.2 * 1. / (1. + numpy.exp(-20 * x))
        return numpy.vstack([brightness, brightness, brightness])


class InputFollowingWave(Effect):
    @classmethod
    def render(cls, x, t, inputs, slider_values):
        # TODO: sliders
        n = x.shape[1]
        brightness = numpy.sin(
            (20 * inputs.focus_x * x - 20 * inputs.focus_y * t))**2
        return numpy.vstack([numpy.zeros((2, n)), brightness])
