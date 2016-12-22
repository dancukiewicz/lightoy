import colorsys
import numpy


class Effect:
    """
    TODO: docstring
    """
    def __init__(self, n_leds):
        pass

    def render(self, x, t, input):
        """
        Determines the brightness and color of an LED at a given point in space
            and time. Multiple effects can be simultaneously used; in that case,
            the final color a given LED will be the sum of the effects.

        Args:
            x: a 1-by-n array representing a set of points in space. The
                location of each point can range from 0 to 1.
            t: the time, in floating point seconds after the server was started.
               Can be assumed to have millisecond accuracy.
            input: An InputState named tuple containing information about the
               current input.
        Returns:
            An 3-by-n array repreAsenting the desired R, G, and B values for an
            LED that is present at a given point in space. These should range
            from 0 to 1.
        """
        raise "Not implemented"


class HsvEffect(Effect):
    def render_hsv(self, x, t, inputs):
        """
        Returns:
            A 3-by n array representing the desired H, S, and V values.
        """
        raise "not implemented"

    def render(self, x, t, inputs):
        # TODO: will this ever be a perf problem?
        # TODO: This hasn't actually been tested yet
        n = x.shape[1]
        hsv = self.render_hsv(x, t, inputs)
        output = numpy.zeros((3, n))
        for i in range(n):
            h, s, v = hsv[:, i]
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            output[:, i] = [r, g, b]
        return output


class WavyEffect(HsvEffect):
    def __init__(self, n_leds):
        self.periods = numpy.random.rand(n_leds)

    def render_hsv(self, x, t, inputs):
        # TODO: params
        n = x.shape[1]
        # Default: just make everything red, with a bit of a wavy effect.
        brightness_modulation = (
            numpy.sin(t * 10 * self.periods))
        brightness = ((0.8 - 0.1 * inputs.fade)
                      + (0.2 + 0.1 * inputs.fade) * brightness_modulation)
        pos_mask = numpy.sin((x - inputs.focus_x) * 5)**8

        h = (0.5 + 0.5 * numpy.sin(inputs.focus_y * 2)) * numpy.ones((1, n))
        s = 0.8 * numpy.ones((1, n))
        v = ((0.25 + 0.75 * inputs.fade) *
             numpy.multiply(brightness, pos_mask))
        return numpy.vstack([h, s, v])


class March(Effect):
    """
    Subtle marching effect.
    """
    def render(self, x, t, inputs):
        # TODO: params
        n = x.shape[1]
        brightness = numpy.sin(
            (20 * inputs.focus_x * x - 20 * inputs.focus_y * t))**2
        return numpy.vstack([numpy.zeros((2, n)), brightness])







