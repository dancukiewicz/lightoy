class SerialOutput(object):
    """
    Outputs LED colors via a serial interface.

    The assumption is that the serial device is a Teensy board with the
    firmware being that compiled from teensy/lightoy_arduino.ino.
    """
    OUT_HEADER = bytes("head", 'utf-8')

    def __init__(self, serial_device, num_leds, baud=115200):
        self.serial_device = serial_device
        self.num_leds = num_leds
        self.baud = baud

    def output(self, colors):
        """colors: NUM_LEDS x 3 array, representing the GRB color values for
        each LED in the [0..1] range."""
        out_data = self._get_out_data(colors)

    def _get_out_data(self, colors):
        out_data = bytearray(self.out_header)
        for led in range(self.num_leds):
            # The LED at the end is at x=0, which is simply an artifact of how I
            # laid them out now.
            # TODO: huh? what's that mean?
            r, g, b = colors[:, self.num_leds - led - 1]
            out_data.append(int(g * 255))
            out_data.append(int(r * 255))
            out_data.append(int(b * 255))
        return out_data
