import numpy

from effects.effect import Effect


class VerticalWipe(Effect):
    @classmethod
    def render(cls, X, t, t_diff, inputs, param, state):
        x = X[0, :]
        brightness = 0.2 * 1. / (1. + numpy.exp(-20 * x))
        return numpy.vstack([brightness, brightness, brightness])


class InputFollowingWave(Effect):
    # TODO: add some sliders

    @classmethod
    def render(cls, x, t, t_diff, inputs, param, state):
        n = x.shape[1]
        brightness = numpy.sin(
            (20 * inputs.focus_x * x - 20 * inputs.focus_y * t))**2
        return numpy.vstack([numpy.zeros((2, n)), brightness])
