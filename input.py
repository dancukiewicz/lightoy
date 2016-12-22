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

TOUCH_HIST_LENGTH = 15

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
        # Represents the (x,y,t) locations of the previous touch locations.
        self.touch_history = numpy.zeros((3, TOUCH_HIST_LENGTH))
        # The number of previous consecutive state updates in which there was
        # an active touch.
        self.n_last_touched = 0

        # Fade in/out effect. Increases from 0 to 1 when touch is applied,
        # and then drops to 0 when touch is released.
        self.fade = 0.
        # The idea is for this to be something people can move around, with
        # momentum.
        # TODO: should it have mass when being moved around?
        self.focus_x = 0.
        self.focus_y = 0.
        # For simulating momentum.
        self.x_velocity = 0.
        self.y_velocity = 0.
        # This records the value of the focus point when the touch was first
        # applied.
        # TODO: more clear comment
        self.focus_x_offset = 0.
        self.focus_y_offset = 0.

        self.last_t = None

    def get_state(self, t):
        """"
        This is called frequently, before every render cycle.

        Returns:
            An InputState namedtuple that contains the inputs to the rendering
            logic.
        """
        if self.last_t:
            dt = t - self.last_t
        else:
            dt = 0
        self.last_t = t

        # Load the touches so that they're consistent
        touches = self.cur_touches

        if touches:
            touch = touches[0]
            self.focus_x = touch['x'] + self.focus_x_offset
            self.focus_y = touch['y'] + self.focus_y_offset
            self.fade += 0.02
        else:
            self.fade -= 0.005
            #
            if self.n_last_touched > 1:
                # TODO: describe how we don't want to use too-recent history
                if self.n_last_touched > 10:
                    last_i = 10
                else:
                    last_i = self.n_last_touched - 1

                # Touch was applied in at least two previous frames, and was
                # just released.
                diffs = self.touch_history[:, 0] - self.touch_history[:, last_i]
                t_dx, t_dy, t_dt = diffs
                if t_dt <= 0:
                    raise "hey, it does happen"

                # TODO: param
                max_velocity = 3.

                self.x_velocity = t_dx / t_dt
                if abs(self.x_velocity) > max_velocity:
                    self.x_velocity = numpy.sign(self.x_velocity) * max_velocity

                self.y_velocity = t_dy / t_dt
                if abs(self.y_velocity) > max_velocity:
                    self.y_velocity = numpy.sign(self.y_velocity) * max_velocity

                print (self.x_velocity, self.y_velocity)

            else:
                # friction
                resistance = 0.5
                self.x_velocity *= (1. - resistance * dt)
                self.y_velocity *= (1. - resistance * dt)
                self.focus_x += self.x_velocity * dt
                self.focus_y += self.y_velocity * dt
            self.n_last_touched = 0

        self.fade = numpy.clip(self.fade, 0.0, 1.0)

        return InputState(focus_x=self.focus_x,
                          focus_y=self.focus_y,
                          fade=self.fade)

    # TODO: These are not atomic; this is bad.
    def on_touch_start(self, touches, t):
        """
        Args:
            touches: a list of dicts with 'x' and 'y' fields, ranging from
                     0 to 1.
        """
        touch = touches[0]
        self._update_touch_history(touch['x'], touch['y'], t)
        self.focus_x_offset = self.focus_x - touch['x']
        self.focus_y_offset = self.focus_y - touch['y']
        self.cur_touches = touches

    def on_touch_move(self, touches, t):
        touch = touches[0]
        self._update_touch_history(touch['x'], touch['y'], t)
        self.cur_touches = touches

    def on_touch_end(self, t):
        self.cur_touches = []

    def on_touch_cancel(self, t):
        return self.on_touch_end(t)

    def _update_touch_history(self, x, y, t):
        self.touch_history = numpy.roll(self.touch_history, 1, 1)
        self.touch_history[:, 0] = [x, y, t]
        self.n_last_touched += 1
