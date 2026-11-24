#include <Wire.h>

void setup() {
    // note: you might have to press the reset button next to usb-c port on arduino to get this to show
    Serial.begin(115200);
    while (!Serial);
    Wire.begin();
    Serial.println("Scanning...");

    for (byte addr = 1; addr < 127; addr++) {
        Wire.beginTransmission(addr);
        if (Wire.endTransmission() == 0) {
            Serial.print("Found device at 0x");
            Serial.println(addr, HEX);
        }
    }
    Serial.println("Done");
}

void loop() {

}