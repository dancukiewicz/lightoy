import numpy


class Parameter(object):
    """
    A parameter holds a value that can be changed at any time by the user.
    Parameters are used by effects to determine how they're drawn.
    Additionally, there are global parameters that are applicable to every
    effect.

    Parameters can also have actions, which are functions that mutate the
    value in the parameter.
    """
    # Each parameter instance keeps a value object.
    value = None

    # Dict of (string => function) representing the actions that can be
    # performed for the effect. The corresponding function is called with
    # self as the only argument.
    actions = {}

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def do_action(self, action_name):
        if action_name not in self.actions:
            print("Requested action (%s) not found in actions for %s"
                  % (action_name, self.__class__.__name__))
        self.actions[action_name](self)


class Scalar(Parameter):
    """Defines a mutable scalar parameter that goes into an effect,
    along with its current state."""
    actions = {"reset": lambda self: self.on_reset()}

    def __init__(self, min_value, max_value, default_value):
        self.min_value = min_value
        self.max_value = max_value
        self.default_value = default_value
        self.value = default_value

    def on_reset(self):
        self.value = self.default_value

    def set_value(self, value):
        if value < self.min_value or value > self.max_value:
            # TODO: logging
            print("Value given (%f) can't exceed bounds [%f, %f]" %
                            (value, self.min_value, self.max_value))
            value = numpy.clip(value, self.min_value, self.max_value)

        return super(Scalar, self).set_value(value)


class Array(Parameter):
    actions = {"reset": lambda self: self.reset()}

    def __init__(self, shape, reset_fn=None):
        self.shape = shape
        self.reset_fn = reset_fn
        self.reset()

    def reset(self):
        if self.reset_fn is not None:
            self.value = self.reset_fn()
        else:
            self.value = numpy.zeros(self.shape)


class RandomArray(Array):
    """The value is a random Array where each component is uniformly
    distributed."""
    actions = {"reset": lambda self: self.reset()}

    def __init__(self, shape):
        if type(shape) is not tuple:
            shape = (shape,)

        def reset_fn():
            return numpy.random.rand(*shape)
        super(RandomArray, self).__init__(shape, reset_fn)
