import cv2
import numpy as np
from matplotlib import pyplot as plt
import os
import pandas as pd
import scipy.optimize

cur_dir = os.path.dirname(os.path.realpath(__file__))
points = pd.read_csv(os.path.join(cur_dir, "data/locations.csv"))
# y is flipped to make y increasing
points['y'] *= -1
# x is flipped so that the spiral goes clockwise up
points['x'] *= -1

# x, y: locations of LEDs in 3-space (pix)
#    note: this assumes that there's no projection going on
#    also assumes that each LED is about one turn further than the last one
# average_f: average dy/d(theta) (pix/rad)
# r: radius of cylinder (pix)
# x_c: the x-coordinate of the center of the cylinder (pix)


def estimate_location(x, last_theta, last_y, average_f, r, x_c):
    """Returns (theta, y) tuple of expected location of light.
    last_theta and last_y can be None if this is the first point.
    """
    ratio = (x - x_c) / r
    ratio = np.clip(ratio, -1, 1)
    theta = -np.arccos(ratio)
    if last_theta is not None:
        # Adjust theta so that it's as close as possible to one turn further
        # than the last estimate.
        b = np.round((last_theta - theta) / (2 * np.pi)) + 1
        theta += 2 * np.pi * b
    if last_y is not None:
        y = last_y + average_f * (theta - last_theta)
    else:
        y = 0
    return theta, y


def get_error(points, average_f, r, x_c):
    """Returns the error (MSE between measured and estimated
    y-coordinates of points) given the parameters."""
    last_theta = None
    last_y = None
    squared_error_sum = 0
    for i, row in points.iterrows():
        estimated_theta, estimated_y = estimate_location(
            row['x'], last_theta, last_y, average_f, r, x_c)
        ground_y = row['y'] - points['y'][0]
        squared_error_sum += (estimated_y - ground_y) ** 2
        last_theta, last_y = estimated_theta, estimated_y
    return squared_error_sum / len(points)





def find_optimal_values(points):
    """Returns (average_f, r, x_c) tuple."""

    # best guess for f: delta-y / delta-theta
    delta_y = points['y'][points.index[-1]] - points['y'][0]
    delta_theta = 2 * np.pi * (len(points) - 1)
    f_guess = delta_y / delta_theta
    f_bounds = (0.97 * f_guess, 1.03 * f_guess)

    # TODO: even more arbitrary - this is taken straight from the photo.
    x_bounds = (-2820., -1620.)
    r_guess = (x_bounds[1] - x_bounds[0]) / 2
    r_bounds = (r_guess - 200, r_guess + 200)

    x_c_guess = (x_bounds[0] + x_bounds[1]) / 2.
    # TODO: this is totally arbitrary.
   # x_c_bounds = (x_center - 500, x_center + 500)

    def find_min_parameter(name, bounds, err_fn, n=1000):
        values = np.linspace(bounds[0], bounds[1], n)
        errs = [err_fn(value) for value in values]
        plt.figure()
        plt.plot(values, errs)
        plt.savefig(os.path.join(cur_dir, "out/%s.png" % name))
        min_value = values[errs.index(min(errs))]
        print("%s:" % name, min_value)
        return min_value

    print("f:", f_guess, "r:", r_guess, "x_c:", x_c_guess)

#    results = scipy.optimize.fmin_tnc(
#        lambda x: get_error(points, x[0], r_guess, x[1]),
#        [f_guess, x_c_guess],
#        approx_grad=True,
#        bounds=[f_bounds, (x_c_min - 500, x_c_min + 500)],
#        callback=lambda x: print(x))

    for i in range(10):
        image = cv2.imread(os.path.join(cur_dir, "data/photo.jpg"))
        draw_spiral(image, f_guess, r_guess, x_c_guess, points['y'][0])
        cv2.imwrite(os.path.join(cur_dir, "out/spiral_%d.jpg" % i), image)
        f_guess = find_min_parameter(
            "f_%d" % i, (f_guess * 0.97, f_guess * 1.03),
            lambda f: get_error(points, f, r_guess, x_c_guess))
        x_c_guess = find_min_parameter(
            "x_c_%d" % i, (x_c_guess - 500, x_c_guess + 500),
            lambda x_c: get_error(points, f_guess, r_guess, x_c))



    return f_guess, r_guess, x_c_guess


def draw_spiral(image, f, r, x_c, y_0):
    max_theta = 2 * np.pi * (len(points) - 1)
    for theta in np.linspace(0, max_theta, 5000):
        x = -(x_c + r * np.cos(theta))
        y = -(y_0 + f * theta)
        if np.sin(theta) <= 0:
            cv2.circle(image, (int(x), int(y)), 5, (0,0,255), -1)


f, r, x_c = find_optimal_values(points)



