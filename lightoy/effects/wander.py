import numpy

from lightoy.effects import Effect
import lightoy.params


class Wander(Effect):
    """
    Each LED is initialized with a vector in RGB-space with an identical length
    and random direction.

    The color is incremented by the vector. If one of the colors reaches the
    low or high bound, the sign of that component of the vector is reversed.

    Basically, it's like that 2D screen saver with some logo bouncing around the
    screen, but here it's a color bouncing around in 3D color space.
    """
    def init_params(self):
        return {
            'speed': lightoy.params.Scalar(0., 2., 0.3),
            }

    def init_state(self):
        directions = numpy.zeros((3, self.n_leds))
        for i in range(self.n_leds):
            v = numpy.random.rand(3)
            v = (v / numpy.linalg.norm(v))
            directions[:, i] = v

        return {
            'colors': numpy.zeros((3, self.n_leds)),
            'directions': directions
        }

    @classmethod
    def update_state(cls, x, t, t_diff, inputs, param, state):
        n_leds = x.shape[1]
        colors = state['colors']
        directions = state['directions']
        colors += (directions * t_diff * param['speed'].get_value())
        for c in range(3):
            for led in range(n_leds):
                if colors[c, led] < 0:
                    colors[c, led] *= -1
                    directions[c, led] *= -1
                elif colors[c, led] > 1:
                    colors[c, led] = 2 - colors[c, led]
                    directions[c, led] *= -1

    @classmethod
    def render(cls, x, t, t_diff, inputs, param, state):
        return state['colors'].copy()
