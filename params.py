import numpy

class Param:
    # Dict of (string => function) representing the actions that can be
    # performed for the effect. The corresponding function is called with
    # self as an argument.
    actions = {}

    def do_action(self, action_name):
        if action_name not in self.actions:
            print("Requested action (%s) not found in actions for %s"
                  % (action_name, self.__class__.__name__))
        self.actions[action_name](self)

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value


class Scalar(Param):
    """Defines a mutable scalar parameter that goes into an effect, along with its
    current state."""
    actions = {"reset": lambda self: self.on_reset()}

    def __init__(self, name, min_value, max_value, default_value):
        self.min_value = min_value
        self.max_value = max_value
        self.name = name
        self.default_value = default_value
        self.value = default_value

    def on_reset(self):
        self.value = self.default_value

    def set_value(self, value):
        if value < self.min_value or value > self.max_value:
            raise Exception("Value given (%f) can't exceed bounds [%f, %f]" %
                            (value, self.min_value, self.max_value))
        return super(Scalar, self).set_value(value)


class RandomArray(Param):
    """The value is a random Array where each component is uniformly
    distributed."""
    actions = {"reset": lambda self: self.reset()}

    def __init__(self, name, shape):
        self.name = name
        self.shape = shape
        self.value = numpy.zeros(shape)
        self.reset()

    def reset(self):
        self.value = numpy.random.rand(*self.shape)
