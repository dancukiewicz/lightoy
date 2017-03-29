import numpy

from effects.effect import Effect


class VerticalWipe(Effect):
    @classmethod
    def render(cls, x, t, t_diff, inputs, param, state):
        brightness = 0.2 * 1. / (1. + numpy.exp(-20 * x[0, :]))
        return numpy.vstack([brightness, brightness, brightness])


class InputFollowingWave(Effect):
    # TODO: add some sliders

    @classmethod
    def render(cls, x, t, t_diff, inputs, param, state):
        n = x.shape[1]
        brightness = numpy.sin(
            (20 * inputs.focus_x * x[0, :] - 20 * inputs.focus_y * t))**2
        return numpy.vstack([numpy.zeros((2, n)), brightness])
2