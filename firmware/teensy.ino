/* 
 * This firmware is designed to be used with a Teensy 3.x board. It uses the
 * OctoWS2811 library to drive an array of WS2811 LEDs. I would recommend using
 * this with the OctoWS2811 adapter:
 *
 * https://www.pjrc.com/store/octo28_adaptor.html
 *
 * It listens on the USB UART and waits for the host to
 * send a predefined header ("head"), followed by the 3-byte GRB color values
 * of the individual LEDs. At this point, the Teensy pushes the color values
 * to the LED array. The OctoWS2811 library does the heavy lifting in terms of
 * communication.
 */
 
#include <OctoWS2811.h>

const int kNumLeds = 250;

DMAMEM int displayMemory[kNumLeds * 6];
int drawingMemory[kNumLeds * 6];

OctoWS2811 leds(kNumLeds, displayMemory, drawingMemory,
                WS2811_GRB | WS2811_800kHz);

void setup() {
  leds.begin();
  Serial.begin(115200); // USB is always 12 Mbit/sec
}

// The header that is expected before every frame of input data.
const String kHeader = "head";

// The number of header
unsigned int headerBytesParsed = 0;

// 24-bit GRB value for each pixel.
char dataBuffer[kNumLeds * 3];

void loop() {
  if (Serial.available()) {
    // Read bytes one by one until we found that we've read the entire header.
    char input = Serial.read();
    if (input == kHeader[headerBytesParsed]) {
      // We received the expected header byte.
      headerBytesParsed++;
    } else {
      // The byte did not match the expected header byte, so
      // start over.
      headerBytesParsed = 0;
    }
    if (headerBytesParsed >= kHeader.length()) {
      // Once we've encountered the proper header, read the LED color values.
      headerBytesParsed = 0;
      unsigned int numBytes = kNumLeds * 3;
      if (Serial.readBytes(dataBuffer, numBytes) == numBytes) {
        for (int led = 0; led < kNumLeds; led++) {
          int color =
              ((int)dataBuffer[3 * led]     << 16) +
              ((int)dataBuffer[3 * led + 1] << 8) +
              ((int)dataBuffer[3 * led + 2]);
          leds.setPixel(led, color);
        }
        leds.show();
      }
    }
  }
}

