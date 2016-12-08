import collections
import numpy

# Represents the state variables that go into the rendering logic.
# Every spatial dimension should range from 0 to 1, in order to be consistent
# with the LED dimensions.
INPUT_DIMS = [
    'focus_x',  # float
    'focus_y',  # float
    'fade'      # float, from 0 to 1
]

TOUCH_HIST_LENGTH = 3

InputState = collections.namedtuple('InputState', INPUT_DIMS)


class InputProcessor:
    """
    Keeps track of input state and calculates functions based on input.

    Note on thread-safety: All of the "on..." methods are called from one
    thread, while the "get_state" method is called from another thread.

    Every 't' argument is the time in seconds since the server was started.
    """
    def __init__(self):
        # List of current touches, each a dict with 'x' and 'y' fields.
        self.cur_touches = []
        # Fade in/out effect. Increases from 0 to 1 when touch is applied,
        # and then drops to 0 when touch is released.
        self.fade = 0.
        # The idea is for this to be something people can move around, with
        # mass.
        # TODO: should it have mass when being moved around?
        self.focus_x = 0
        self.focus_y = 0

        # Represents the (x,y,t) locations of the previous touch locations.
        self.touch_history = numpy.zeros((3, TOUCH_HIST_LENGTH))
        pass

    def get_state(self, t):
        """"
        This is called frequently, before every render cycle.

        Returns:
            An InputState namedtuple that contains the inputs to the rendering
            logic.
        """
        if self._is_touched():
            touch = self.cur_touches[0]
            self.focus_x = touch['x']
            self.focus_y = touch['y']
            self.touch_history = numpy.roll(self.touch_history, 1, 1)
            self.touch_history[:, 0] = [touch['x'], touch['y'], t]
            self.fade += 0.01
        else:
            self.fade -= 0.002

        self.focus_x = numpy.clip(self.focus_x, 0.0, 1.0)
        self.focus_y = numpy.clip(self.focus_y, 0.0, 1.0)
        self.fade = numpy.clip(self.fade, 0.0, 1.0)

        return InputState(focus_x=self.focus_x,
                          focus_y=self.focus_y,
                          fade=self.fade)

    def on_touch_start(self, touches, t):
        """
        Args:
            touches: a list of dicts with 'x' and 'y' fields, ranging from
                     0 to 1.
        """
        self.cur_touches = touches

    def on_touch_move(self, touches, t):
        self.cur_touches = touches

    def on_touch_end(self, t):
        self.cur_touches = []

    def on_touch_cancel(self, t):
        return self.on_touch_end(t)

    def _is_touched(self):
        return len(self.cur_touches) > 0
