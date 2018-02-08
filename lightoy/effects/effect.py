class Effect(object):
    """
    An Effect is responsible for what to draw on the LED array, given
    the input state, parameters and LED locations. render() performs the magic;
    every effect should implement this.

    An effect can have per-effect parameters, which the user can then tweak
    in real time via the UI. init_params() should be overridden to provide any
    desired parameters.

    Additionally, an effect can have a state, which is represented by a dict.
    init_state() can be overridden to set the initial state, and update_state()
    can be overridden to update the state before each rendering action.
    """
    # Dictionary of (parameter name => stateful Parameter instance)
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

    def do_render(self, x, t, t_diff, inputs):
        """Updates the effect's state and renders the lights
        (see doc on render()) with the effect's stored parameters and state."""
        self.update_state(x, t, t_diff, inputs, self.params, self.state)
        return self.render(x, t, t_diff, inputs, self.params, self.state)

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

        This method is stateless. do_render() should be called for an
        effect instance to render with the effect's state.

        Args:
            x: a 3-by-n array representing a set of points in space.
               Each dimension can range from -1 to 1.
            t: the time, in floating point seconds after the server was started.
               Can be assumed to have millisecond accuracy.
            input: An InputState named tuple containing information about the
               current input.
            param: A (name => Parameter) dictionary of the per-effect
                parameters.
        Returns:
            An 3-by-n array representing the desired R, G, and B values for an
            LED that is present at a given point in space. These should range
            from 0 to 1.
        """
        raise Exception("Not implemented")
