#include <Servo.h>

Servo servos[7];
int pins[7] = {1, 2, 3, 4, 5, 6, 7}; // TODO: FILL THESE OUT PROPERLY
int servoMap[][] = {
  {1000, 1590, 0, 1}, // grabber
  {600, 2350, -170, 170}, // wrist roll
  {600, 2350, -170, 170}, // wrist pitch
  {1000, 1000, 0, 0}, // elbow
  {560, 2340, -170, 170}, // shoulder 1
  {560, 2340, -170, 170} // shoulder 2
};

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < servos.length; i++) {
    servos[i].attach(pins[i]);
  }
}

void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');
    double angles[7];

    int startI = 0;    
    for (int i = 0; i < 7; i++) {
      int endI = data.indexOf(" ");
      angles[i] = data.substring(startI, endI).toDouble();

      startI = endI + 1;
      Serial.print(angles[i]);
      Serial.print(",");
    }
    angles[6] = -angles[5];

    Serial.print(" | ");

    int pwms[] = mapAngleToPwm(angles);
    
    for (int i = 0; i < pwms.length; i++) {
      // servos[i].writeMicroseconds(pwms[i]);
      Serial.print(pwms[i]);
      Serial.print(",");
    }
  }

}

int[] mapAngleToPwm(int angles[]) {
  int pwms[angles.length];
  for (int i = 0; i < angles.length; i++) {
    double a = servoMap[i][0];
    double b = servoMap[i][1];
    double t = (angles[i] - servoMap[i][2]) / (servoMap[i][3] - servoMap[i][2]);
    pwms[i] = (int)(a + (b - a) * t);
  }
  return pwms;
}