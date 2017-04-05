import numpy


def cartesian_to_cylindrical(xyz):
    """Args:
        xyz: A 3-by-n array representing the x,y,z coordinates.

    Returns: A 3-by-n array tuple representing the r,theta,h coordinates.
    """
    n = xyz.shape[1]
    rth = numpy.zeros((3, n))
    for i in range(n):
        x, y, z = xyz[:, i]
        r = numpy.sqrt(x**2 + y**2)
        theta = numpy.arctan2(y, x)
        h = z
        rth[:, i] = [r, theta, h]
    return rth
