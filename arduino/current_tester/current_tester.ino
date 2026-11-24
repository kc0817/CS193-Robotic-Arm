#include <Wire.h>
#include <Adafruit_INA219.h>

Adafruit_INA219 currentSensor;

void setup() {
    Serial.begin(9600);
    while (!Serial);

    if (!currentSensor.begin()) {
        Serial.println("Current sensor not found");
        while (true);
    }
    currentSensor.setCalibration_32V_1A();
}

void loop() {
    float current_mA = currentSensor.getCurrent_mA();
    float busV = currentSensor.getBusVoltage_V();
    Serial.print(current_mA);
    Serial.print(" mA, ");
    Serial.print(busV);
    Serial.println(" V");
    delay(50);
}