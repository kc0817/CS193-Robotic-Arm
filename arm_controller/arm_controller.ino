#include <Servo.h>
#include <initializer_list>

const int numServos = 7;
const int shoulder2Index = 5;
bool enabled = true;

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

// measured in degrees/sec
int servoMaxSpeeds[numServos] = {
  -1,
  270,
  180,
  180,
  90,
  90,
  90
};

bool shouldPower[numServos] = {true, true, true, true, true, true, true};
double endTargetAngles[numServos] = {0, 0, 0, 0, 0, 0, 0};
double curTargetAngles[numServos] = {0, 0, 0, 0, 0, 0, 0}; // assumed current angles
unsigned long prevMillis;

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < numServos; i++) {
    servos[i].attach(pins[i]);
  }

  // initiating servos to zero positions
  prevMillis = millis();
  powerServos();
}

void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');

    if (data == "start") {
      enabled = true;
      writeBack({String("Arm enabled")});
    } 
    else if (data == "stop") {
      enabled = false;
      writeBack({String("Arm disabled")});
    } 
    else if (!enabled) {
      writeBack({String("Arm current disabled")});
    } 
    else if (data.length() >= 7 && data.substring(0, 7) == "ch_port") {
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
      writeBack({String("Port move successful")});
  
    } else if (data.length() >= 4 && data.substring(0, 4) == "move") {
      data = data.substring(5);

      for (int i = 0; i < numServos; i++) {
        if (i == shoulder2Index) {
          shouldPower[i] = shouldPower[i-1];
          if (shouldPower[i]) {
            endTargetAngles[i] = -endTargetAngles[i-1];
          }
        } else {
          int endI = data.indexOf(",");
          if (endI == 0) {
            shouldPower[i] = false;
          } else {
            shouldPower[i] = true;
            if (endI == -1) {
              endTargetAngles[i] = data.toDouble();
            } else {
              endTargetAngles[i] = data.substring(0, endI).toDouble();
            }
          }
          data = data.substring(endI+1);
        }
      }
      
      String angleStr = String("angles: ");
      String powerStr = String("should power: ");
      for (int i = 0; i < numServos; i++) {
        angleStr += endTargetAngles[i] + String(", ");
        powerStr += shouldPower[i] + String(", ");
      }
      writeBack({angleStr, powerStr});
    } else {
      writeBack({String("Invalid Serial message: ") + data});
    }
  }
  powerServos();
}

void powerServos() {
  unsigned long curMillis = millis();
  for (int i = 0; i < numServos; i++) {
    if (shouldPower[i]) {
      double lookahead = servoMaxSpeeds[i] * ((curMillis - prevMillis) / 1000);
      double error = endTargetAngles[i] - curTargetAngles[i];
      if (abs(error) <= .001) {
        curTargetAngles[i] = endTargetAngles[i];
        shouldPower[i] = false;
      } else if (abs(error) <= lookahead) {
        curTargetAngles[i] = endTargetAngles[i];
      } else {
        curTargetAngles[i] += signof(error) * lookahead;
      }
    }
  }
  prevMillis = curMillis;

  int pwms[numServos];
  mapAnglesToPwms(curTargetAngles, pwms);
  for (int i = 0; i < numServos; i++) {
    if (shouldPower[i]) {
      servos[i].writeMicroseconds(pwms[i]);
    }
  }
}

void writeBack(std::initializer_list<String> data) {
  Serial.println(data.size());
  for (const String& d : data) {
    Serial.println(d);
  }
}

void mapAnglesToPwms(double angles[], int pwms[]) {
  for (int i = 0; i < numServos; i++) {
    double a = servoMap[i][0];
    double b = servoMap[i][1];
    double t = calcLerpT(angles[i], servoMap[i][2], servoMap[i][3]);
    t = constrain(t, 0, 1);
    pwms[i] = (int)lerp(a, b, t);
  }
}

double lerp(double a, double b, double t) {
  return a + (b - a) * t;
}
double calcLerpT(double n, double a, double b) {
  return (n - a) / (b - a);
}
int signof(double n) {
  if (n > 0) {
    return 1;
  }
  if (n < 0) {
    return -1;
  }
  return 0;
}

int indexOf(int n, const int list[], int size) {
  for (int i = 0; i < size; i++) {
    if (list[i] == n) {
      return i;
    }
  }
  return -1;
}