import colorsys
import numpy


"""Color utilities. All color inputs are 3-by-n arrays."""


def color_convert(orig, convert_fn):
    """
    convert_fn should be a function that accepts a 3-tuple of the color
        in original color space and returns a 3-tuple in new color space.
    """
    n = orig.shape[1]
    new = numpy.zeros((3, n))
    for i in range(n):
        point = orig[:, i]
        new_point = convert_fn(point[0], point[1], point[2])
        new[:, i] = new_point
    return new


def rgb_to_hsv(rgb):
    return color_convert(rgb, colorsys.rgb_to_hsv)


def hsv_to_rgb(hsv):
    return color_convert(hsv, colorsys.hsv_to_rgb)


def gamma_correct(rgb, gamma):
    hsv = rgb_to_hsv(rgb)
    hsv[2, :] **= gamma
    return hsv_to_rgb(hsv)
