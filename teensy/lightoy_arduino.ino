/* 
 * 
 * TODO: license, etc
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

// TODO: describe protocol, or point to location in other repo where
// it's described

// The header that is expected before every frame of input data.
const String kHeader = "head";

// The number of header
unsigned int headerBytesParsed = 0;

// 24-bit GRB value for each pixel.
char dataBuffer[kNumLeds * 3];


// perform mapping sequence:
// flash every 10th LED red for 100 ms
// flash LEDs sequentially for 36 ms each in g,b,r sequence
// flash every 10th LED blue for 5s

const int kRed =   0x0000ff;
const int kGreen = 0xff0000;
const int kBlue =  0x00ff00;

void calib_loop() {
  for (int led = 0; led  < kNumLeds; led++) {
    if (led % 10 == 11) {
      leds.setPixel(led, kBlue);
    } else {
      leds.setPixel(led, 0);
    }
  }
  leds.show();
  delay(100);
  for  (int activeLed = 0; activeLed < kNumLeds; activeLed++) {
    for (int led = 0; led < kNumLeds; led++) {
      int color;
      if (led == activeLed) {
        switch (led % 3) {
          case 0:
            color = kGreen;
            break;
          case 1:
            color = kBlue;
            break;
          case 2:
          default:
            color = kRed;
            break;
        } 
      } else {
        color  = 0;
      }
      leds.setPixel(led, color);
    }
    leds.show();
    delay(36);
  }
  for (int led = 0; led  < kNumLeds; led++) {
    if (led % 3 == 0) {
      leds.setPixel(led, kRed);
    } else {
      leds.setPixel(led, 0);
    }
  }
  leds.show();
  delay(5000);
}

// 
void loop() {
  if (Serial.available()) {
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

