"""Program to draw virtual LEDs in order to visualize the array without
the hardware.

TODO: finish this.
"""


import math
import numpy
from OpenGL.GLU import *
from OpenGL.GL import *
import pygame
import redis


def lamp_coordinates():
    strips = 9
    leds_per_strip = 50
    # distance between LEDs (cm)
    pitch = 1
    # radius of lamp ring (cm)
    radius = 10
    coords = numpy.zeros((strips * leds_per_strip, 3))
    for strip in range(strips):
        theta = 2 * math.pi / strips * strip
        x = radius * math.cos(theta)
        y = radius * math.sin(theta)
        for led in range(leds_per_strip):
            z = led * pitch
            coords[strip * leds_per_strip + led, :] = [x, y, z]
    return coords


def init_display(resolution):
    pygame.init()
    pygame.display.set_mode(resolution, DOUBLEBUF | OPENGL)
    aspect = resolution[0] / resolution[1]
    gluPerspective(45, aspect, 0.1, 50.0)
    glTranslatef(0.0, 0.0, -10)


def draw_sphere():
    glBegin(GL_LINES)
    # TODO: do the drawing
    glEnd()


def render(coordinates):
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    for x, y, z in coordinates:
        glTranslatef(x, y, z)
        draw_sphere()
        glTranslatef(-x, -y, -z)
    pygame.display.flip()


def main():
    client = redis.Redis("localhost", "6379")
    init_display((1280, 960))
    coordinates = lamp_coordinates()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        render(coordinates)
        pygame.time.wait(10)  # TODO: remove once pub-subbing


if __name__ == "__main__":
    main()
