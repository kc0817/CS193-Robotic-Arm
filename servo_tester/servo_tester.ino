#include <Servo.h>

Servo s1;
int s1Pin = 6;

Servo s2;
int s2Pin = 5;

void setup() {
  Serial.begin(9600);
  s1.attach(s1Pin);
  s2.attach(s2Pin);
  delay(500);
}

void loop() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    int n = data.toInt();
    Serial.print("received ");
    Serial.println(n);
    s1.writeMicroseconds(constrain(n, 550, 2400));
    s2.writeMicroseconds(constrain(550, mapShoulder(n), 2400));
  }
}
int mapShoulder(int n) {
  return (int)(-.999474 * n + 2915.89974);
}

// grabber close: 1590
// grabber open: 1000

// wrist roll: 600, 2350
// wrist pitch: 600, 2400
// elbow: broken
// shoulder regression: -.999474x - 2915.89974