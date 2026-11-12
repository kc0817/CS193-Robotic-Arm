#include <Servo.h>

const int numServos = 7;
const int shoulder2Index = 5;

Servo servos[numServos];
int pins[numServos] = {2, 3, 4, 5, 6, 7, 8}; // TODO: FILL THESE OUT PROPERLY
int servoMap[numServos][4] = {
  {1000, 1590, 0, 1}, // grabber
  {560, 2350, -82, 82}, // wrist roll
  {560, 2350, -105, 60 }, // wrist pitch
  {1000, 1000, 0, 0}, // elbow
  {560, 2350, -82, 82}, // shoulder 1 4 is actually 0  
  {560, 2340, -82, 82}, // shoulder 2 already centered
  {560, 2350, -82, 82} // turret
}; // range of turret: -82.04 to +82.04

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < numServos; i++) {
    servos[i].attach(pins[i]);
  }
}

void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');
    bool shouldPower[numServos];
    double angles[numServos];

    Serial.println();   
    Serial.print("angles: ");
    for (int i = 0; i < numServos; i++) {
      if (i == shoulder2Index) {
        angles[i] = -angles[i-1];
        shouldPower[i] = shouldPower[i-1];
      } else {
        int endI = data.indexOf(",");
        if (endI == 0) {
          shouldPower[i] = false;
        } else {
          shouldPower[i] = true;
          if (endI == -1) {
            angles[i] = data.toDouble();
          } else {
            angles[i] = data.substring(0, endI).toDouble();
          }
        }
        data = data.substring(endI+1);
      }
      Serial.print(angles[i]);
      Serial.print(",");
    }
    Serial.println();

    int pwms[numServos];
    mapAngleToPwm(angles, pwms);
    
    Serial.print("should power: ");
    for (int i = 0; i < numServos; i++) {
      Serial.print(shouldPower[i]);
      Serial.print(",");
    }
    Serial.println();
    Serial.print("pwms: ");
    for (int i = 0; i < numServos; i++) {
      if (shouldPower[i]) {
        servos[i].writeMicroseconds(pwms[i]);
        Serial.print(pwms[i]);
      }
      Serial.print(",");
    }
    Serial.println();
  }
}

void mapAngleToPwm(double angles[], int pwms[]) {
  for (int i = 0; i < numServos; i++) {
    double a = servoMap[i][0];
    double b = servoMap[i][1];
    double t = (angles[i] - servoMap[i][2]) / (servoMap[i][3] - servoMap[i][2]);
    t = constrain(t, 0, 1);
    pwms[i] = (int)(a + (b - a) * t);
  }
}