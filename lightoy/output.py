import serial


class Output(object):
    """Base class that defines how to output the LED colors. This is responsible
    for communicating with any external devices."""
    def output(self, colors):
        """
        Outputs the rendered LED colors.

        Args:
            colors: 3 x NUM_LEDS array, representing the RGB color values for
                each LED in the [0..1] range.
        """
        raise Exception("not implemented")


class DummyOutput(object):
    def output(self, colors):
        pass


class SerialOutput(Output):
    """
    Outputs LED colors via a serial interface.

    The protocol is custom and simple. Every time the host wants to render, it
    sends a fixed header ("head" in this case), and then for each of
    the LEDs, it sends three bytes representing the G, R and B color values.

    The assumption is that the serial device is a Teensy board with the
    firmware being that compiled from teensy/lightoy_arduino.ino.
    """
    OUT_HEADER = bytes("head", 'utf-8')

    def __init__(self, serial_device_name, baud=115200):
        self.serial_device_name = serial_device_name
        self.baud = baud
        self.serial = serial.Serial(
            self.serial_device_name,
            self.baud,
            timeout=None,
            write_timeout=None,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
            inter_byte_timeout=None)

    def output(self, colors):
        out_data = self._get_out_data(colors)
        self.serial.write(out_data)
        self.serial.flush()

    def _get_out_data(self, colors):
        out_data = bytearray(self.OUT_HEADER)
        num_leds = colors.shape[1]
        for led in range(num_leds):
            r, g, b = colors[:, num_leds - led - 1]
            out_data.append(int(g * 255))
            out_data.append(int(r * 255))
            out_data.append(int(b * 255))
        return out_data
