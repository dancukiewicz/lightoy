import numpy


class LocationModel(object):
    """A LocationModel is used to obtain the 3D position of each LED. This
    information can (but doesn't have to be) then be used by the Effect for
    rendering.

    Of course, the location of all the LEDs may not be known, but an approximate
    answer might be useful.
    """
    def get_locations(self, session):
        """Returns a 3-by-N array representing locations of the LEDs
        in the x,y,z dimensions. Each dimension should range from -1 to 1.
        """
        raise Exception("Not implemented")


class Spiral(LocationModel):
    """Produces locations for a strip of LEDs arranged in a spiral.
    """
    def __init__(self, num_leds):
        self.num_leds = num_leds

    def get_locations(self, session):
        # orientation of spiral, looking from the top
        # 1 for counterclockwise, -1 for clockwise
        orientation = -1
        # How many total twists there are in the spiral. This is a tunable
        # parameter since I've found it easier to determine this via tweaking
        # until it looks right.
        twists = session.global_params['twists'].get_value()
        # angle in x-y plane swept between two consequent LEDs
        theta_per_led = 2. * numpy.pi * twists / self.num_leds
        thetas = numpy.array(range(self.num_leds)) * theta_per_led
        locations = numpy.zeros((3, self.num_leds))
        # X
        locations[0, :] = numpy.cos(thetas * orientation)
        # Y
        locations[1, :] = numpy.sin(thetas * orientation)
        # Z
        locations[2, :] = numpy.linspace(-1., 1., self.num_leds)
        return locations
