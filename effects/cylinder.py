import numpy

from effects.effect import Effect
import geometry
import params


class Cylinder(Effect):
    """
    Does a cool wavy thing on a cylinder.
    """
    def init_params(self):
        return {
            'petals': params.Scalar(0., 10., 3.),
            'speed': params.Scalar(0., 100., 1.)
        }

    @classmethod
    def render(cls, xyz, t, t_diff, inputs, param, state):
        rth = geometry.cartesian_to_cylindrical(xyz)
        theta = rth[1, :]
        petals = param['petals'].get_value()
        speed = param['speed'].get_value()
        brightness = 0.3 + 0.5 * numpy.sin(petals * theta + t * speed)
        return numpy.tile(brightness, (3, 1))
