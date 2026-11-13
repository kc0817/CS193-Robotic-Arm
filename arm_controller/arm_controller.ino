#include <Servo.h>
#include <initializer_list>

const int numServos = 7;
const int shoulder2Index = 5;

Servo servos[numServos];
String names[numServos] {
  String("gripper"), 
  String("wrist roll"), 
  String("wrist pitch"), 
  String("elbow"), 
  String("shoulder1"), 
  String("shoulder2"), 
  String("turret")
};
int pins[numServos] = {8, 3, 4, 5, 6, 7, 2}; // TODO: FILL THESE OUT PROPERLY
int servoMap[numServos][4] = {
  {1000, 1590, 0, 1}, // grabber
  {560, 2350, -82, 82}, // wrist roll
  {560, 2350, -105, 60 }, // wrist pitch
  {560, 2350, -82, 82}, // elbow
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

    if (data.length() >= 7 && data.substring(0, 7) == "ch_port") {
      int portSeparator = data.indexOf(" ", 8);
      if (portSeparator == -1) {
        writeBack({String("Invalid ch_port command")});
        return;
      }
      int fromPort = data.substring(8, portSeparator).toInt();
      int toPort = data.substring(portSeparator+1).toInt();

      if (fromPort == 0 || toPort == 0) {
        writeBack({String("Invalid port numbers")});
        return;
      }

      bool portTaken = indexOf(toPort, pins, numServos) != -1;
      if (portTaken) {
        writeBack({String("Port ") + toPort + String(" already taken by ") + names[toPort]});
        return;
      }
      
      int servoI = indexOf(fromPort, pins, numServos);
      if (servoI == -1) {
        writeBack({String("No servo at port ") + fromPort});
        return;
      }
      servos[servoI].detach();
      servos[servoI].attach(toPort);
      pins[servoI] = toPort;
      writeBack({String("Port move successfull")});
  
    } else if (data.length() >= 4 && data.substring(0, 4) == "move") {
      bool shouldPower[numServos];
      double angles[numServos];
      data = data.substring(5);

      for (int i = 0; i < numServos; i++) {
        if (i == shoulder2Index) {
          angles[i] = -angles[i-1];
          shouldPower[i] = shouldPower[i-1];
        } else {
          int endI = data.indexOf(",");
          if (endI == 0) {
            shouldPower[i] = false;
            angles[i] = 100;
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
      }

      int pwms[numServos];
      mapAngleToPwm(angles, pwms);
      
      String angleStr = String("angles: ");
      String powerStr = String("should power: ");
      for (int i = 0; i < numServos; i++) {
        angleStr += angles[i] + String(", ");
        powerStr += shouldPower[i] + String(", ");
      }
      writeBack({angleStr, powerStr});

      for (int i = 0; i < numServos; i++) {
        if (shouldPower[i]) {
          servos[i].writeMicroseconds(pwms[i]);
        }
      }
    } else {
      writeBack({String("Invalid Serial message: ") + data});
    }
  }
}

void writeBack(std::initializer_list<String> data) {
  Serial.println(data.size());
  for (const String& d : data) {
    Serial.println(d);
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

int indexOf(int n, const int list[], int size) {
  for (int i = 0; i < size; i++) {
    if (list[i] == n) {
      return i;
    }
  }
  return -1;
}