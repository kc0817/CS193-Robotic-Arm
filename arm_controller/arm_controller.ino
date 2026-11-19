#include <Servo.h>
#include <initializer_list>
#include <cmath>

const int numServos = 7;
const int shoulder1Index = 4;
const int shoulder2Index = 5;
bool enabled = true;

Servo servos[numServos];
String names[numServos] {
  String("g"), 
  String("wr"), 
  String("wp"), 
  String("e"), 
  String("s"), 
  String("s2"), 
  String("t")
};
int pins[numServos] = {3, 4, 5, 6, 7, 8, 9}; // TODO: FILL THESE OUT PROPERLY
int servoMap[numServos][4] = {
  {1000, 1750, 0, 1}, // grabber
  {560, 2350, -82, 82}, // wrist roll
  {560, 2350, -105, 60 }, // wrist pitch
  {560, 2350, -82, 82}, // elbow
  {560, 2350, -82, 82}, // shoulder 1 4 is actually 0  
  {565, 2345, -82, 82}, // shoulder 2 already centered
  {560, 2350, -82, 82} // turret
}; // range of turret: -82.04 to +82.04

// measured in degrees/sec
int servoMaxSpeeds[numServos] = {
  -1,
  -1,
  150,
  70,
  45,
  45,
  150
};
double speedPercentage = 1;

bool shouldPower[numServos] = {true, true, true, true, true, true, true};
double endTargetAngles[numServos] = {0, 0, 0, 0, 0, 0, 0};
double curTargetAngles[numServos] = {0, 0, 0, 0, 0, 0, 0}; // assumed current angles
double lookaheads[numServos] = {0, 0, 0, 0, 0, 0, 0};
unsigned long prevMicros;
const double TIME_STEP = .0083;

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < numServos; i++) {
    servos[i].attach(pins[i]);
  }

  // initiating servos to zero positions
  prevMicros = micros();
  powerServosRaw(endTargetAngles);
}

void loop() {
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');

    if (data == "get_angles") {
      String curTargets = "";
      String endTargets = "";
      String la = "";
      for (int i = 0; i < numServos; i++) {
        curTargets += curTargetAngles[i] + String(", ");
        endTargets += (std::round(endTargetAngles[i]*10)/10.) + String(", ");
        la += lookaheads[i] + String(", ");
      }
      writeBack({curTargets, endTargets, la});
    }
    
    else if (data == "start") {
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
  
    } 

    else if (data.length() >= 5 && data.substring(0, 5) == "speed") {
      speedPercentage = constrain(data.substring(6).toDouble(), 0, 1);
      writeBack({String("Set speed to ") + speedPercentage});
    }

    //label_move g 0,t 1,
    else if (data.length() >= 10 && data.substring(0, 10) == "label_move") {
      String remaining = data.substring(11);
      int endI = remaining.indexOf(",");
      bool success = true;
      while (endI != -1) {
        String joint_cmd = remaining.substring(0, endI);
        int spaceI = joint_cmd.indexOf(" ");
        String joint_name = joint_cmd.substring(0, spaceI);
        int jointI = -1;
        for (int i = 0; i < numServos; i++) {
          if (names[i] == joint_name) {
            jointI = i;
            break;
          }
        }
        if (jointI == -1) {
          writeBack({String("Joint ") + joint_name + String(" invalid for label move command: ") + data + String(", wth remaming=") + remaining + String("; and endI=") + endI});
          success = false;
          break;
        }
        endTargetAngles[jointI] = constrain(joint_cmd.substring(spaceI+1).toDouble(), servoMap[jointI][2], servoMap[jointI][3]);
        shouldPower[jointI] = true;
        if (jointI == shoulder1Index) {
          endTargetAngles[shoulder2Index] = -endTargetAngles[jointI];
          shouldPower[shoulder2Index] = true;
        }

        remaining = remaining.substring(endI+1);
        endI = remaining.indexOf(",");
      }

      if (success) {
        String angleStr = String("angles: ");
        String powerStr = String("should power: ");
        for (int i = 0; i < numServos; i++) {
          angleStr += endTargetAngles[i] + String(", ");
          powerStr += shouldPower[i] + String(", ");
        }
        writeBack({angleStr, powerStr});
      }
    }

    else if (data.length() >= 4 && data.substring(0, 4) == "move") {
      data = data.substring(5);

      for (int i = 0; i < numServos; i++) {
        if (i == shoulder2Index) {
          shouldPower[i] = shouldPower[shoulder1Index];
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
            endTargetAngles[i] = constrain(endTargetAngles[i], servoMap[i][2], servoMap[i][3]);
          }
          data = data.substring(endI+1);
        }
      }

      // powerServosRaw(endTargetAngles);
      
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
  unsigned long curMicros = micros();
  float dt = (curMicros - prevMicros) / 1e6;
  if (dt < TIME_STEP) {
    return;
  }
  prevMicros = curMicros;
  for (int i = 0; i < numServos; i++) {
    if (shouldPower[i]) {
      if (servoMaxSpeeds[i] <= 0) {
        curTargetAngles[i] = endTargetAngles[i];
      }
      float lookahead = servoMaxSpeeds[i] * speedPercentage * dt;
      lookaheads[i] = lookahead;
      double error = endTargetAngles[i] - curTargetAngles[i];
      if (abs(error) <= lookahead) {
        curTargetAngles[i] = endTargetAngles[i];
      } else {
        curTargetAngles[i] += signof(error) * lookahead;
      }
    }
  }

  powerServosRaw(curTargetAngles);

  for (int i = 0; i < numServos; i++) {
    if (shouldPower[i] && abs(endTargetAngles[i] - curTargetAngles[i]) < .001) {
      shouldPower[i] = false;
    }
  }
}
void powerServosRaw(const double angles[]) {
  int pwms[numServos];
  mapAnglesToPwms(angles, pwms);
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

void mapAnglesToPwms(const double angles[], int pwms[]) {
  for (int i = 0; i < numServos; i++) {
    double a = servoMap[i][0];
    double b = servoMap[i][1];
    double t = calcLerpT(angles[i], servoMap[i][2], servoMap[i][3]);
    t = constrain(t, 0, 1);
    pwms[i] = (int)lerp(a, b, t);
  }
}

double lerp(const double a, const double b, const double t) {
  return a + (b - a) * t;
}
double calcLerpT(const double n, const double a, const double b) {
  return (n - a) / (b - a);
}
int signof(const double n) {
  if (n > 0) {
    return 1;
  }
  if (n < 0) {
    return -1;
  }
  return 0;
}

int indexOf(const int n, const int list[], const int size) {
  for (int i = 0; i < size; i++) {
    if (list[i] == n) {
      return i;
    }
  }
  return -1;
}