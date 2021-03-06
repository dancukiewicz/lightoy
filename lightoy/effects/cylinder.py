import numpy

import lightoy.color
from lightoy.effects import Effect
import lightoy.geometry
import lightoy.params


class Cylinder(Effect):
    """
    Does a cool wavy thing on a cylinder.
    """
    def init_params(self):
        return {
            't_shift': lightoy.params.Scalar(0., 100., 2.),
            'h_shift': lightoy.params.Scalar(0., 100., 1.),
            't_period': lightoy.params.Scalar(0., 100., 2.),
            'h_period': lightoy.params.Scalar(0., 100., 4.),

            'speed': lightoy.params.Scalar(0., 100., 2.)
        }

    @classmethod
    def render(cls, xyz, t, t_diff, inputs, param, state):
        rth = lightoy.geometry.cartesian_to_cylindrical(xyz)
        theta = rth[1, :]
        h = rth[2, :]
        t_shift = param['t_shift'].get_value()
        h_shift = param['h_shift'].get_value()
        t_period = param['t_period'].get_value()
        h_period = param['h_period'].get_value()
        speed = param['speed'].get_value()

        hue = 0.5 + 0.3 * (numpy.sin((t_period * theta)
                                     + t_shift * t * (speed - 0.5))
                           + numpy.sin((h_period * h) + h_shift * t * speed))
        sat = 0.5 + 0.3 * (numpy.sin((t_period * theta)
                                     + t_shift * t * (speed - 0.3))
                           + numpy.sin((h_period * h) + h_shift * t * speed))
        val = 0.5 + 0.5 * (numpy.sin((t_period * theta)
                                     + t_shift * t * (speed - 0.1))
                           + numpy.sin((h_period * h) + h_shift * t * speed))
        hsv = numpy.vstack([hue, sat, val])
        return lightoy.color.hsv_to_rgb(hsv)
