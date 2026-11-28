#include <Servo.h>
#include <Adafruit_INA219.h>
#include <initializer_list>

const int numServos = 7;
const int shoulder1Index = 1;
const int shoulder2Index = 2;
const int grabberI = 6;
bool enabled = true;

Servo servos[numServos];
String names[numServos] {
  String("t"),
  String("s"), 
  String("s2"), 
  String("e"), 
  String("wp"), 
  String("wr"), 
  String("g")
};
int pins[numServos] = {9, 8, 7, 6, 5, 4, 3}; // TODO: FILL THESE OUT PROPERLY
const float servoMap[numServos][4] = {
  {560, 2350, -82, 82}, // turret
  {2350, 550, -80, 84}, // shoulder 1 4 is actually 0  
  {565, 2345, -82, 82}, // shoulder 2 NEED TO RETUNE IF GOING TO USE
  {2350, 560, -82, 82}, // elbow
  {560, 2350, -76, 88 }, // wrist pitch
  {560, 2350, -82, 82}, // wrist roll
  {1400, 2150, 0, 1} // grabber
};

// measured in degrees/sec
int servoMaxSpeeds[numServos] = {
  150,
  60,
  60,
  70,
  150,
  -1,
  -1
};
float speedPercentage = 1;


Adafruit_INA219 currentSensor;
bool currentSensorFound = false;
const float graspCurrentThreshold_mA = 100; // TODO: tune this
bool grabberClosing = false;
const float grabberClosingSpeed = .5;
float grabberCurrent = 0;

bool moveBlocking = false;

bool shouldPower[numServos] = {true, true, true, true, true, true, true};
float endTargetAngles[numServos] = {0, 0, 0, 0, 0, 0, 0};
float curTargetAngles[numServos] = {0, 0, 0, 0, 0, 0, 0}; // assumed current angles
float absAngles[numServos] = {0, 0, 0, 0, 0, 0, 0}; // absolute joint angles
int locked[numServos] = {0, 0, 0, 0, 0, 0, 0};
unsigned long prevMicros;
const float TIME_STEP = .0083;

void setup() {
  Serial.begin(9600);

  for (int i = 0; i < numServos; i++) {
    servos[i].attach(pins[i]);
  }

  currentSensorFound = currentSensor.begin();
  if (currentSensorFound) {
    currentSensor.setCalibration_32V_1A();
  }

  // initiating servos to zero positions
  prevMicros = micros();
  powerServosRaw(endTargetAngles);
}

void loop() {
  grabberCurrent = currentSensor.getCurrent_mA();
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');

    if (data == "get_angles") {
      String curTargets = "";
      String endTargets = "";
      for (int i = 0; i < numServos; i++) {
        curTargets += curTargetAngles[i] + String(", ");
        endTargets += (round(endTargetAngles[i]*10)/10.) + String(", ");
      }
      writeBack({curTargets, endTargets});
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
    
    else if (data.substring(0, 7) == "ch_port") {
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

    else if (data.substring(0, 5) == "speed") {
      speedPercentage = constrain(data.substring(6).toDouble(), 0, 10);
      writeBack({String("Set speed to ") + speedPercentage});
    }
    else if (data == "check_grabber_current") {
      writeBack({String("closing: ") + grabberClosing + String(", current: ") + grabberCurrent + String(" mA")});
    }
    // gc for grabber close in current sensing mode
    else if (data == "gc") {
      if (!currentSensorFound) {
        writeBack({String("no current sensor found")});
      }
      else {
        grabberClosing = true;
        endTargetAngles[grabberI] = 0;
        shouldPower[grabberI] = false;
        writeBack({String("closing grabber")});
      }
    }
    else if (data.substring(0, 4) == "lock") {
      int in = indexOf(data.substring(5), names, numServos);
      locked[in] = 1;
      shouldPower[in] = true;
      if (in == shoulder1Index) {
        locked[shoulder2Index] = 1;
      shouldPower[shoulder2Index] = true;
      }
      writeBack({String("locked joint ") + names[in]});
    }
    else if (data.substring(0, 6) == "unlock") {
      int in = indexOf(data.substring(7), names, numServos);
      locked[in] = 0;
      shouldPower[in] = false;
      if (in == shoulder1Index) {
        locked[shoulder2Index] = 0;
        shouldPower[shoulder2Index] = false;
      }
      writeBack({String("unlocked joint ") + names[in]});
    }
    else if (data == "get_locks") {
      String lockStr = "";
      for (int i = 0; i < numServos; i++) {
        lockStr += locked[i] + String(",");
      }
      writeBack({lockStr});
    }

    else if (data.substring(0, 4) == "move") {
      moveBlocking = data.substring(0, 13) == "move_blocking";
      data = data.substring(data.indexOf(" ")+1);


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
          } 
          else if (locked[i]) {
            writeBack({String("cannot move ") + names[i] + String(" because it's locked")});
            return;
          }
          else {
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
      
      if (!moveBlocking) {
        String angleStr = String("angles: ");
        String powerStr = String("should power: ");
        for (int i = 0; i < numServos; i++) {
          angleStr += endTargetAngles[i] + String(", ");
          powerStr += shouldPower[i] + String(", ");
        }
        writeBack({angleStr, powerStr});
      }
      
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

  if (endTargetAngles[grabberI] != 0) {
    grabberClosing = false;
  }
  if (grabberClosing) {
    float error = endTargetAngles[grabberI] - curTargetAngles[grabberI];

    if (abs(error) < .001) {
      grabberClosing = false;
    } 
    else if (grabberCurrent < graspCurrentThreshold_mA) {
      float lookahead = grabberClosingSpeed * dt * speedPercentage;
      curTargetAngles[grabberI] += min(lookahead, abs(error)) * signof(error);

      float t = constrain(calcLerpT(curTargetAngles[grabberI], servoMap[grabberI][2], servoMap[grabberI][3]), 0, 1);
      int pwm = (int)lerp(servoMap[grabberI][0], servoMap[grabberI][1], t);
      servos[grabberI].writeMicroseconds(pwm);
    }
  }
  float lookaheads[numServos] = {0, 0, 0, 0, 0, 0, 0};
  for (int i = 0; i < numServos; i++) {
    // want custom powering logic for locked joints
    if (locked[i]) {
      // TODO fill out custom powering logic for these locked joints
      if (names[i] == "e") {
        endTargetAngles[i] -= lookaheads[shoulder1Index];
        curTargetAngles[i] = endTargetAngles[i];
        lookaheads[i] = -lookaheads[shoulder1Index];
      } else if (names[i] == "wp") {
        endTargetAngles[i] -= lookaheads[shoulder1Index] + lookaheads[i-1];
        curTargetAngles[i] = endTargetAngles[i];
      }
    }
    
    // don't want to normally power the grabber when its in teh current sensing closing mode
    else if (shouldPower[i] && (!grabberClosing || grabberI != i)) {
      if (servoMaxSpeeds[i] <= 0) {
        curTargetAngles[i] = endTargetAngles[i];
      }
      float lookahead = servoMaxSpeeds[i] * speedPercentage * dt;
      float error = endTargetAngles[i] - curTargetAngles[i];
      if (abs(error) <= lookahead) {
        curTargetAngles[i] = endTargetAngles[i];
        lookaheads[i] = error;
      } else {
        curTargetAngles[i] += signof(error) * lookahead;
        lookaheads[i] = lookahead * signof(error);
      }
    }
  }

  powerServosRaw(curTargetAngles);

  bool allDone = true;
  for (int i = 0; i < numServos; i++) {
    if (shouldPower[i]) {
      if (abs(endTargetAngles[i] - curTargetAngles[i]) < .001) {
        shouldPower[i] = false;
      }
      else {
        allDone = false;
      }
    }
  }
  if (moveBlocking && allDone) {
    moveBlocking = false;
    writeBack({String("movement done")});
  }
  
}
void powerServosRaw(const float angles[]) {
  int pwms[numServos];
  mapAnglesToPwms(angles, pwms);
  for (int i = 0; i < numServos; i++) {
    if (shouldPower[i] || locked[i]) {
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

void mapAnglesToPwms(const float angles[], int pwms[]) {
  for (int i = 0; i < numServos; i++) {
    float a = servoMap[i][0];
    float b = servoMap[i][1];
    float t = calcLerpT(angles[i], servoMap[i][2], servoMap[i][3]);
    t = constrain(t, 0, 1);
    pwms[i] = (int)lerp(a, b, t);
  }
}

float lerp(const float a, const float b, const float t) {
  return a + (b - a) * t;
}
float calcLerpT(const float n, const float a, const float b) {
  return (n - a) / (b - a);
}
int signof(const float n) {
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
int indexOf(const String s, const String list[], const int size) {
  for (int i = 0; i < size; i++) {
    if (list[i] == s) {
      return i;
    }
  }
  return -1;
}