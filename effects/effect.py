import colorsys
import numpy


class Effect:
    """
    TODO: docstring
    """
    # Dictionary of (parameter name => stateful parameter instance)
    params = {}

    # Dictionary representing the effect's state. No restrictions currently.
    state = {}

    def __init__(self, n_leds):
        self.n_leds = n_leds
        self.params = self.init_params()
        self.state = self.init_state()

    def init_params(self):
        """
        Returns the effect's initial parameters.
        """
        return {}

    def init_state(self):
        """
        Returns the effect's initial state.
        """
        return {}

    @classmethod
    def update_state(cls, x, t, t_diff, inputs, param, state):
        """Use this to mutate the state dict."""
        pass

    @classmethod
    def render(cls, x, t, t_diff, inputs, param, state):
        """
        Determines the brightness and color of an LED at a given point in space
            and time. Multiple effects can be simultaneously used; in that case,
            the final color a given LED will be the sum of the effects.

        This method is stateless. render_with_state() should be called for an
        effect instance to render with the effect's state.

        Args:
            x: a 3-by-n array representing a set of points in space.
               Each dimension can range from -1 to 1.
            t: the time, in floating point seconds after the server was started.
               Can be assumed to have millisecond accuracy.
            input: An InputState named tuple containing information about the
               current input.
            params: TODO
        Returns:
            An 3-by-n array representing the desired R, G, and B values for an
            LED that is present at a given point in space. These should range
            from 0 to 1.
        """
        raise "Not implemented"

    @classmethod
    def hsv_to_rgb(cls, hsv):
        """
        Args:
            hsv: A 3-by-n array representing the HSV colors of each light.

        Returns: A 3-by-n array representing the corresponding RGB colors.
        """
        n = hsv.shape[1]
        rgb = numpy.zeros((3, n))
        for i in range(n):
            h, s, v = hsv[:, i]
            r, g, b = colorsys.hsv_to_rgb(h, s, v)
            rgb[:, i] = [r, g, b]
        return rgb


