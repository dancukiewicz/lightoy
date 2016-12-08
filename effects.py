import colorsys
import numpy

class Effect:
    """
    TODO: docstring
    """
    def __init__(self, n_leds):
        pass

    def render(self, x, t):
        """
        Determines the brightness and color of an LED at a given point in space
            and time. Multiple effects can be simultaneously used; in that case,
            the final color a given LED will be the sum of the effects.

        Args:
            x: a 1-by-n array representing a set of points in space. The
                location of each point can range from 0 to 1.
            t: the time, in floating point seconds after the server was started.
               Can be assumed to have millisecond accuracy.
        Returns:
            An 3-by-n array representing the desired R, G, and B values for an
            LED that is present at a given point in space. These should range
            from 0 to 1.
        """
        raise "Not implemented"


class HsvEffect(Effect):
    def render_hsv(self, x, t):
        """
        Returns:
            A 3-by n array representing the desired H, S, and V values.
        """
        raise "not implemented"

    def render(self, x, t):
        # TODO: will this ever be a perf problem?
        # TODO: This hasn't actually been tested yet
        n = x.shape[1]
        hsv = self.render_hsv(x, t)
        output = numpy.zeros((3, n))
        for i in range(n):
            h, s, v = hsv[:, i]
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            output[:, i] = [r, g, b]


class WavyEffect(Effect):
    def __init__(self, n_leds):
        self.periods = numpy.random.rand(n_leds)

    def render(self, x, t):
        n = x.shape[1]
        # Default: just make everything red, with a bit of a wavy effect.
        brightness_modulation = 0.2 * numpy.sin(t * 10 * self.periods)
        brightness = 0.5 + brightness_modulation
        return numpy.vstack([brightness, numpy.zeros((2, n))])

