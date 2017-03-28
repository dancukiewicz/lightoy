import numpy

from effect import Effect


class Wander(Effect):
    """
    Each LED is initialized with a vector in RGB-space with an identical length
    and random direction.

    The color is incremented by the vector. If one of the colors reaches the
    low or high bound, the sign of that component of the vector is reversed.
    # TODO: write this more coherently
    """
    last_t = None

    def __init__(self, n_leds):
        self.n_leds = n_leds
        self.colors = numpy.ones((3, n_leds))

        self.params = {'directions': }

        self.directions = numpy.zeros((3, n_leds))
        for i in range(n_leds):
            v = numpy.random.rand(3)
            v = (v / numpy.linalg.norm(v))
            self.directions[:, i] = v

    def render(self, x, t, inputs, slider_values):
        if self.last_t:
            t_diff = t - self.last_t
        else:
            t_diff = 0

        self.colors += self.directions * t_diff * slider_values['speed']

        for c in range(3):
            for led in range(self.n_leds):
                if self.colors[c, led] < 0:
                    self.colors[c, led] *= -1
                    self.directions[c, led] *= -1
                elif self.colors[c, led] > 1:
                    self.colors[c, led] = 2 - self.colors[c, led]
                    self.directions[c, led] *= -1

        self.last_t = t
        return self.colors.copy()
